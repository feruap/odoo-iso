# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = 'stock.move'

    amunet_dissolution = fields.Boolean(string='Disolucion', default=False)
    amunet_is_water_solvent = fields.Boolean(
        string='Es agua (solvente)',
        compute='_compute_amunet_is_water_solvent',
        help='True si el componente es agua destilada/bi/tridestilada '
             '(categoria Agua). El agua es el solvente, no se disuelve: no '
             'pide bloque de disolucion ni cuenta para el candado del pH.')

    @api.depends('product_id', 'product_id.categ_id')
    def _compute_amunet_is_water_solvent(self):
        for move in self:
            move.amunet_is_water_solvent = move._amunet_is_water_solvent()

    def _amunet_is_water_solvent(self):
        """Agua como solvente: categoria hoja == 'Agua' (destilada, bi, tri).
        NO incluye 'aguas' que son reactivos (peptonada, desionizada, HPLC),
        que viven en la categoria Reactivo."""
        self.ensure_one()
        categ = self.product_id.categ_id
        return bool(categ) and (categ.name or '').strip().lower() == 'agua'

    amunet_ph_adjustment = fields.Char(string='Ajuste de pH')
    amunet_lot_id = fields.Many2one('stock.lot', string='Lote')

    # Lotes disponibles (con stock > 0) en el almacen de Fabrica para
    # este componente — es decir, en la ubicacion origen del consumo.
    # Sirve para FILTRAR el 'Lote surtido' (amunet_lot_id) y que el
    # almacen no pueda capturar un lote que esta en otro almacen (ej.
    # Burgos). Ver tambien la validacion en write().
    amunet_available_lot_ids = fields.Many2many(
        'stock.lot',
        string='Lotes disponibles en Fabrica',
        compute='_compute_amunet_available_lot_ids',
    )

    @api.depends('product_id', 'location_id')
    def _compute_amunet_available_lot_ids(self):
        Quant = self.env['stock.quant']
        for move in self:
            lots = self.env['stock.lot']
            if move.product_id and move.location_id:
                quants = Quant.sudo().search([
                    ('product_id', '=', move.product_id.id),
                    ('location_id', 'child_of', move.location_id.id),
                    ('quantity', '>', 0),
                ])
                lots = quants.lot_id
            move.amunet_available_lot_ids = lots

    # Lista legible de TODOS los lotes realmente reservados/consumidos
    # para este componente, tomados de las operaciones detalladas
    # (move_line_ids), con su cantidad. Complementa a 'amunet_lot_id'
    # (Lote surtido), que solo puede mostrar UN lote: cuando la reserva
    # nativa toma mas de un lote, aqui se ven todos a primera vista.
    amunet_lotes_reales = fields.Text(
        string='Lotes surtidos (reales)',
        compute='_compute_amunet_lotes_reales',
        help='Todos los lotes realmente tomados para este componente, con '
             'su cantidad, segun las operaciones detalladas. Un lote por '
             'renglon (apilados hacia abajo). Si se usa mas de un lote, '
             'aqui aparecen todos.',
    )

    @api.depends('move_line_ids.lot_id', 'move_line_ids.quantity')
    def _compute_amunet_lotes_reales(self):
        for move in self:
            partes = []
            for ml in move.move_line_ids:
                if ml.lot_id and (ml.quantity or 0.0) > 0:
                    partes.append('%s (%s)' % (
                        ml.lot_id.name, ('%g' % ml.quantity)))
            # Un lote por renglon (apilados hacia abajo, no en linea).
            move.amunet_lotes_reales = '\n'.join(partes)

    # Cantidad que el almacen registra al surtir. Es distinta a
    # 'quantity' (cantidad utilizada/consumida nativa Odoo): esta la
    # captura almacen al entregar, 'quantity' la concilia produccion al
    # validar el surtido o cerrar la MO. Espeja qty_supplied de
    # amunet_material_request_line para mantener vocabulario.
    amunet_qty_supplied = fields.Float(
        string='Cantidad surtida',
        digits='Product Unit',
        copy=False,
    )

    amunet_qty_used = fields.Float(
        string='Cantidad utilizada',
        digits='Product Unit',
        copy=False,
        help='Cantidad real consumida en producción. Se captura durante la conciliación.',
    )

    amunet_qty_surplus = fields.Float(
        string='Sobrante',
        compute='_compute_amunet_qty_surplus',
        digits='Product Unit',
        store=False,
    )

    @api.depends('amunet_qty_supplied', 'amunet_qty_used')
    def _compute_amunet_qty_surplus(self):
        for move in self:
            surplus = (move.amunet_qty_supplied or 0.0) - (move.amunet_qty_used or 0.0)
            move.amunet_qty_surplus = max(surplus, 0.0)

    amunet_line_lot_id = fields.Many2one(
        'stock.lot', string='Lote (real)',
        compute='_compute_amunet_line_lot_id',
        inverse='_inverse_amunet_line_lot_id',
        help='Lote realmente usado, capturable EN LA MISMA LINEA (soluciones). '
             'Escribe/actualiza el lote del movimiento (move_line unico).')

    @api.depends('move_line_ids.lot_id')
    def _compute_amunet_line_lot_id(self):
        for move in self:
            lots = move.move_line_ids.mapped('lot_id')
            move.amunet_line_lot_id = lots[0].id if len(lots) == 1 else False

    def _inverse_amunet_line_lot_id(self):
        for move in self:
            lot = move.amunet_line_lot_id
            if not lot:
                continue
            move._amunet_check_preflight_gate()
            mls = move.move_line_ids
            if len(mls) > 1:
                # dejar una sola linea (captura inline = 1 lote por componente)
                (mls[1:]).sudo().unlink()
                mls = move.move_line_ids
            if mls:
                mls[0].sudo().lot_id = lot.id
            else:
                self.env['stock.move.line'].sudo().create({
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'product_uom_id': move.product_uom.id,
                    'lot_id': lot.id,
                    'quantity': move.amunet_qty_used or 0.0,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                })

    amunet_needs_surtido = fields.Boolean(
        string='Requiere surtido',
        compute='_compute_amunet_needs_surtido',
        help='Solo soluciones: True si el componente NO va al Almacen de '
             'reactivos en uso (ARU), es decir es una SUB-SOLUCION que si se '
             'pide por surtido. Los reactivos/agua (van a ARU) son material '
             'directo y NO requieren surtido (solo se captura la utilizada).')

    @api.depends('product_id',
                 'raw_material_production_id.amunet_is_solution_product',
                 'raw_material_production_id.product_id')
    def _compute_amunet_needs_surtido(self):
        for move in self:
            mo = move.raw_material_production_id
            is_sol = mo and (mo.route_type == 'solution'
                             or mo.amunet_is_solution_product)
            if not is_sol:
                move.amunet_needs_surtido = False
                continue
            categ = move.product_id.categ_id
            routes = (categ._amunet_routes_to_aru()
                      if categ and hasattr(categ, '_amunet_routes_to_aru')
                      else False)
            move.amunet_needs_surtido = not routes

    # Flag de UI: True si el usuario actual puede editar la cantidad
    # teorica (product_uom_qty) y la utilizada (quantity). Almacen puro
    # NO debe modificarlas; solo produccion. Mery tiene ambos grupos en
    # staging asi que sigue pudiendo editar.
    amunet_user_can_edit_consume = fields.Boolean(
        string='Puede editar consumo',
        compute='_compute_amunet_user_can_edit_consume',
    )

    @api.depends_context('uid')
    def _compute_amunet_user_can_edit_consume(self):
        user = self.env.user
        can_edit = (
            user.has_group('amunet_production.group_production_supervisor')
            or user.has_group('amunet_production.group_production_operator')
            or user.has_group('mrp.group_mrp_user')
        )
        for rec in self:
            rec.amunet_user_can_edit_consume = can_edit

    # Flag de UI: True si el usuario actual es de Almacen. Solo almacen
    # (Veronica, Patricia, Karla...) puede capturar Cantidad surtida y Lote.
    amunet_user_is_warehouse = fields.Boolean(
        string='Es de almacen',
        compute='_compute_amunet_user_is_warehouse',
    )

    @api.depends_context('uid')
    def _compute_amunet_user_is_warehouse(self):
        is_wh = (
            self.env.user.has_group('amunet_material_request.group_material_warehouse')
            or self.env.user.has_group('amunet_material_request.group_material_manager')
        )
        for rec in self:
            rec.amunet_user_is_warehouse = is_wh

    def _amunet_solution_bom_locked_moves(self):
        """Reactivos de una MO de SOLUCION con BoM definido: sus lineas (que
        reactivos) son FIJAS -> no se pueden agregar/borrar/cambiar. La cantidad
        real usada SI se captura (amunet_qty_used)."""
        return self.filtered(
            lambda m: m.raw_material_production_id
            and m.raw_material_production_id.bom_id
            and (m.raw_material_production_id.route_type == 'solution'
                 or m.raw_material_production_id.amunet_is_solution_product))

    def _amunet_check_preflight_gate(self):
        """Soluciones: no permitir colocar lote (real) ni registrar pesado si el
        preflight de la orden NO esta validado (aceptado). Aplica a TODAS las
        soluciones. Se omite en su o contexto interno."""
        if self.env.su or self.env.context.get('amunet_skip_preflight_gate'):
            return
        for move in self:
            prod = move.raw_material_production_id
            if (prod and prod.amunet_is_solution_product
                    and not prod.amunet_preflight_accepted):
                raise UserError(_(
                    'Antes de colocar lotes o registrar pesados en %s, valida el '
                    'preflight de la orden: usa "Validar piloto" y luego "Aceptar '
                    'para piloto".') % (prod.name or ''))

    def write(self, vals):
        if 'amunet_qty_used' in vals:
            self._amunet_check_preflight_gate()
        # Candado: en soluciones con BoM no se puede CAMBIAR el reactivo de una
        # linea (product_id). Cantidades/lote/consumo si (otros candados).
        if ('product_id' in vals and not self.env.su
                and not self.env.context.get('amunet_supply_internal')):
            if self._amunet_solution_bom_locked_moves():
                raise UserError(_(
                    'No se puede cambiar el reactivo de una linea de una '
                    'solucion con receta (BoM) definida. Las lineas de '
                    'reactivos son fijas.'))
        # Candado: solo Almacen puede capturar 'Cantidad surtida' y 'Lote'
        # del material de una orden de produccion. Produccion nunca.
        # Se omite en escrituras internas del flujo (contexto/sudo).
        supply_fields = {'amunet_qty_supplied', 'amunet_lot_id'}
        if (supply_fields & set(vals)
                and not self.env.su
                and not self.env.context.get('amunet_supply_internal')):
            is_wh = (
                self.env.user.has_group('amunet_material_request.group_material_warehouse')
                or self.env.user.has_group('amunet_material_request.group_material_manager')
            )
            if not is_wh and any(m.raw_material_production_id for m in self):
                raise UserError(_(
                    'Solo personal de Almacen (Veronica, Patricia, Karla) puede '
                    'capturar la Cantidad surtida y el Lote del material.'))
        # Validacion: el 'Lote surtido' debe existir (con stock) en el
        # almacen de Fabrica (ubicacion origen del consumo). Evita que se
        # capture un lote que esta en otro almacen (ej. Burgos) y que no
        # coincide con lo que realmente se reserva/consume.
        if ('amunet_lot_id' in vals and vals.get('amunet_lot_id')
                and not self.env.su
                and not self.env.context.get('amunet_supply_internal')):
            lot = self.env['stock.lot'].browse(vals['amunet_lot_id'])
            for m in self:
                if not m.raw_material_production_id or not m.location_id:
                    continue
                disponible = self.env['stock.quant'].sudo().search_count([
                    ('product_id', '=', m.product_id.id),
                    ('lot_id', '=', lot.id),
                    ('location_id', 'child_of', m.location_id.id),
                    ('quantity', '>', 0),
                ])
                if not disponible:
                    raise UserError(_(
                        'El lote %(lot)s no esta disponible en el almacen de '
                        'Fabrica (%(loc)s). Selecciona un lote que exista en '
                        'Fabrica para surtir %(prod)s.'
                    ) % {
                        'lot': lot.name,
                        'loc': m.location_id.complete_name,
                        'prod': m.product_id.display_name,
                    })
        # Candado: la 'Cantidad por consumir' (product_uom_qty) de un
        # componente NO se puede ajustar una vez que la orden esta
        # planificada (confirmada en adelante). Por nadie. Se omite en
        # escrituras internas del flujo (sudo/contexto).
        if ('product_uom_qty' in vals
                and not self.env.su
                and not self.env.context.get('amunet_supply_internal')):
            for m in self:
                mo = m.raw_material_production_id
                if mo and mo.state != 'draft':
                    raise UserError(_(
                        'No se puede ajustar la cantidad por consumir: la orden '
                        '%s ya esta planificada.') % mo.name)
        res = super().write(vals)
        # Sincroniza el 'quantity' nativo (consumo real) con la 'Cantidad
        # utilizada' cada vez que se captura/edita. Asi el consumo registrado
        # y el check de cierre (button_mark_done, que valida quantity) usan
        # siempre el valor real capturado, aunque se edite la Cantidad
        # utilizada DESPUES de conciliar. Reentrada controlada por contexto.
        if 'amunet_qty_used' in vals and not self.env.context.get('amunet_skip_qty_sync'):
            for m in self:
                used = m.amunet_qty_used or 0.0
                if (m.raw_material_production_id and used > 0
                        and abs((m.quantity or 0.0) - used) > 0.0001):
                    m.sudo().with_context(amunet_skip_qty_sync=True).write(
                        {'quantity': used})
        return res

    def unlink(self):
        # Se PERMITE quitar componentes que aun NO se han consumido, en
        # cualquier estado de la orden (por si un material no es necesario
        # para una produccion). Solo se bloquea un componente ya CONSUMIDO
        # (movimiento hecho) para no romper la trazabilidad de lo usado.
        # Se omite en flujos internos (sudo / contexto).
        if not self.env.su and not self.env.context.get('amunet_supply_internal'):
            # NOTA: NO se bloquea aqui el borrado de lineas de reactivos de
            # soluciones. La proteccion contra que el OPERADOR borre lineas la da
            # la vista (delete deshabilitado para soluciones). Un candado backend
            # de unlink rompia la VALIDACION/produccion, porque el sistema borra y
            # recrea movimientos internamente al confirmar/producir (no es el
            # usuario). Cambiar el reactivo (product_id) si se bloquea en write().
            bloqueados = self.filtered(
                lambda m: m.raw_material_production_id and m.state == 'done')
            if bloqueados:
                raise UserError(_(
                    'No se puede quitar un componente ya CONSUMIDO (movimiento '
                    'hecho): %(prod)s. Solo se pueden quitar materiales que aun '
                    'no se han consumido.'
                ) % {'prod': ', '.join(bloqueados.mapped('product_id.display_name'))})
        return super().unlink()

    amunet_is_valid = fields.Boolean(
        string='Valido',
        compute='_compute_amunet_is_valid',
        store=True,
        help='Automatico: cantidad dentro del rango de pesaje y disolucion confirmada si aplica.'
    )

    @api.depends('quantity', 'product_uom_qty', 'product_id', 'product_id.categ_id', 'amunet_dissolution', 'raw_material_production_id.product_id.categ_id')
    def _compute_amunet_is_valid(self):
        for move in self:
            qty_used = move.quantity
            product = move.product_id

            if qty_used < 0:
                move.amunet_is_valid = False
                continue

            # Cantidad utilizada = 0: el material se entrego pero NO se uso
            # (se devuelve todo en la conciliacion). Es un estado VALIDO, no
            # invalido. La conciliacion es obligatoria antes de cerrar, asi que
            # un 0 aqui es una captura deliberada, no un olvido.
            if not qty_used:
                move.amunet_is_valid = True
                continue

            # Detectar si la MO es de tipo Solucion (categoria del
            # producto a fabricar contiene 'solucion'). Solo en ese
            # flujo aplican los checks estrictos de rango de pesaje y
            # disolucion. Para kits y otros productos, basta con que
            # la cantidad utilizada sea > 0.
            mo_product = move.raw_material_production_id.product_id
            categ = mo_product.categ_id if mo_product else False
            categ_name = (categ.complete_name or categ.name or '') if categ else ''
            es_solucion = 'solucion' in categ_name.lower()

            if not es_solucion:
                # Kit / otro: validez = cantidad utilizada positiva
                move.amunet_is_valid = True
                continue

            # Flujo Solucion: check de rango de pesaje + disolucion
            qty_required = move.product_uom_qty
            range_text = (product.product_tmpl_id.amunet_weighing_range_text or '') if product else ''
            delta = 0.0
            if range_text:
                match = re.search(r'[\d]+\.?[\d]*', range_text)
                if match:
                    try:
                        delta = float(match.group())
                    except ValueError:
                        delta = 0.0

            if delta > 0:
                in_range = (qty_required - delta) <= qty_used <= (qty_required + delta)
            else:
                in_range = qty_used > 0

            # El agua es el solvente: no se disuelve, no exige la marca.
            if not move.amunet_dissolution and not move._amunet_is_water_solvent():
                move.amunet_is_valid = False
                continue

            move.amunet_is_valid = in_range

    def _amunet_check_single_lot_per_component(self):
        """Candado ISO 13485: cada componente de una orden de produccion debe
        consumir de UN SOLO lote. A primera vista la linea muestra un lote,
        pero en el detalle puede haber 2-3 (split automatico de Odoo cuando un
        lote no alcanza la cantidad). Aqui se bloquea ese caso.

        Solo aplica a ordenes NUEVAS: creadas despues del cutoff configurado en
        el parametro 'amunet.single_lot_cutoff'. Sin cutoff, el candado no
        aplica (rule off), para no bloquear ordenes previas en curso."""
        cutoff = self.env['ir.config_parameter'].sudo().get_param(
            'amunet.single_lot_cutoff')
        cutoff_dt = fields.Datetime.to_datetime(cutoff) if cutoff else None
        if not cutoff_dt:
            return
        problemas = []
        for move in self.filtered(
            lambda m: m.raw_material_production_id
            and m.state not in ('draft', 'cancel')
        ):
            mo = move.raw_material_production_id
            # Solo ordenes creadas despues de activar el candado.
            if mo.create_date and mo.create_date <= cutoff_dt:
                continue
            lotes = move.move_line_ids.filtered(
                lambda ml: ml.lot_id and ml.quantity > 0
            ).mapped('lot_id')
            if len(lotes) > 1:
                problemas.append('  - %s (orden %s): lotes %s' % (
                    move.product_id.display_name,
                    mo.name,
                    ', '.join(lotes.mapped('name')),
                ))
        if problemas:
            raise UserError(_(
                'Solo se permite UN lote por componente en la orden de '
                'produccion (trazabilidad ISO 13485). Estos componentes tienen '
                'mas de un lote cargado:\n%(det)s\n\nAjusta el surtido/detalle '
                'para dejar un solo lote por componente antes de cerrar.'
            ) % {'det': '\n'.join(problemas)})

    def _action_done(self, cancel_backorder=False):
        """Gate SGC de salida: bloquea movimientos que sacan un lote
        fuera del inventario interno (a customer/transit) si el lote
        fue producido por una MO que aun no tiene QC aprobado.

        Aplica solo cuando el producto requiere control de calidad
        (qc_required = True). Para productos sin QC, no afecta.

        ISO 13485 / Cofepris: producto NO se libera al mercado sin
        autorizacion de QC.
        """
        # Candado ISO: un solo lote por componente de la orden de produccion.
        self._amunet_check_single_lot_per_component()
        for move in self:
            if move.location_id.usage != 'internal':
                continue
            if move.location_dest_id.usage not in ('customer', 'transit'):
                continue
            for ml in move.move_line_ids:
                if not ml.lot_id or ml.quantity <= 0:
                    continue
                product = ml.product_id or move.product_id
                if not product.product_tmpl_id.qc_required:
                    continue
                # Buscar la MO que produjo este lote (a traves de
                # lot_producing_ids; usa 'in' porque es Many2many).
                mo = self.env['mrp.production'].sudo().search([
                    ('lot_producing_ids', 'in', ml.lot_id.id),
                ], limit=1)
                if mo and mo.quality_analysis_status != 'approved':
                    raise UserError(_(
                        'No se puede liberar el lote %(lot)s del producto '
                        '%(prod)s. El analisis de calidad del MO %(mo)s '
                        'esta en estado "%(qc)s", no esta aprobado todavia. '
                        'Espera la aprobacion de QC antes de sacar el '
                        'producto del inventario interno.'
                    ) % {
                        'lot': ml.lot_id.name,
                        'prod': product.display_name,
                        'mo': mo.name,
                        'qc': dict(mo._fields['quality_analysis_status'].selection).get(
                            mo.quality_analysis_status, mo.quality_analysis_status
                        ),
                    })
        return super()._action_done(cancel_backorder=cancel_backorder)
