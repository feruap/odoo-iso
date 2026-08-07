# -*- coding: utf-8 -*-
import logging
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from .stock_move import _parse_date

_logger = logging.getLogger(__name__)

CRITERIO_SEL = [('ok', 'Cumple'), ('nok', 'No cumple')]
CRITERIO_SEL_NA = [('ok', 'Cumple'), ('nok', 'No cumple'), ('na', 'N/A')]


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # ── Criterios de aceptación ─────────────────────────────────────────────
    amunet_crit1 = fields.Selection(CRITERIO_SEL, 'Empaque íntegro, sin perforaciones ni daños externos')
    amunet_crit2 = fields.Selection(CRITERIO_SEL, 'Etiqueta legible con información correcta (producto, lote, fechas)')
    amunet_crit3 = fields.Selection(CRITERIO_SEL, 'Sin daños visibles en el material (deformaciones, humedad, etc.)')
    amunet_crit4 = fields.Selection(CRITERIO_SEL_NA, 'Certificado de análisis del proveedor recibido y correcto')
    amunet_crit5 = fields.Selection(CRITERIO_SEL, 'Cantidad recibida coincide con lo solicitado en la orden')
    amunet_crit_obs = fields.Text('Observaciones de inspección')

    # ── Disposición ──────────────────────────────────────────────────────────
    amunet_con_observaciones = fields.Boolean(
        'Con observaciones — requiere revisión de Calidad',
        help='Marca esto si algo llegó en mal estado o con discrepancias. '
             'Quedará registrado y se notificará a Calidad.',
    )

    # ── Resumen de lotes de equipos con seriales ────────────────────────────
    amunet_equipment_lots_html = fields.Html(
        compute='_compute_amunet_equipment_lots_html',
        string='Lotes de equipo',
        store=False,
    )

    @api.depends('move_line_ids.lot_id', 'move_line_ids.lot_id.amunet_serial_ids',
                 'move_line_ids.lot_id.amunet_serial_ids.serial_number')
    def _compute_amunet_equipment_lots_html(self):
        for picking in self:
            if picking.picking_type_code != 'incoming':
                picking.amunet_equipment_lots_html = False
                continue
            direct = picking.move_line_ids.lot_id.filtered('amunet_allow_multi_serial')
            if not direct:
                picking.amunet_equipment_lots_html = False
                continue
            derived = self.env['stock.lot'].search([
                ('amunet_source_lot_id', 'in', direct.ids)
            ])
            all_lots = (direct | derived).sorted('name')
            rows = []
            for lot in all_lots:
                serials = lot.amunet_serial_ids.sorted('serial_number').mapped('serial_number')
                serial_text = ', '.join(serials) if serials else '<em>Sin seriales capturados</em>'
                origen = (f' <span style="color:#6c757d;font-size:12px;">'
                          f'(separado de {lot.amunet_source_lot_id.name})</span>'
                          if lot.amunet_source_lot_id else '')
                rows.append(
                    f'<div style="margin-bottom:4px;">'
                    f'<b>{lot.name}</b>{origen}: {serial_text}'
                    f'</div>'
                )
            picking.amunet_equipment_lots_html = ''.join(rows)

    # ── Firma ────────────────────────────────────────────────────────────────
    amunet_receptor_id = fields.Many2one(
        'res.users', 'Recibió',
        help='Usuario que inspeccionó y validó esta recepción.',
    )

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _get_quarantine_location(self):
        """Ubicación de Control de calidad del almacén de este picking."""
        wh = self.picking_type_id.warehouse_id
        if not wh:
            return self.env['stock.location']
        parent = wh.lot_stock_id.location_id
        return self.env['stock.location'].search([
            ('location_id', '=', parent.id),
            ('usage', '=', 'internal'),
            ('name', 'ilike', 'calidad'),
        ], limit=1)

    # ── Onchange: auto-marcar "con observaciones" si algún criterio falla ──
    @api.onchange('amunet_crit1', 'amunet_crit2', 'amunet_crit3',
                  'amunet_crit4', 'amunet_crit5')
    def _onchange_criterios(self):
        if any(getattr(self, f'amunet_crit{i}') == 'nok' for i in range(1, 6)):
            self.amunet_con_observaciones = True

    # ── action_confirm: asignar destino automático + corregir lote ──────────
    @api.model_create_multi
    def create(self, vals_list):
        pickings = super().create(vals_list)
        for picking in pickings.filtered(lambda p: p.amunet_disposition_qc_id):
            picking._amunet_sync_liberacion_from_original()
        return pickings

    def action_assign(self):
        res = super().action_assign()
        for picking in self.filtered(
            lambda p: p.amunet_disposition_qc_id and p.state == 'assigned'
        ):
            picking._amunet_sync_liberacion_from_original()
        return res

    def _amunet_sync_liberacion_from_original(self):
        """Copia datos del proveedor desde la recepción original al picking de
        liberación de QC (amunet_disposition_qc_id). Así Karla ve los datos
        completos al confirmar el ingreso sin tener que re-capturarlos."""
        self.ensure_one()
        qc = self.amunet_disposition_qc_id
        if not qc or not qc.picking_id:
            return
        orig_pick = qc.picking_id
        for move in self.move_ids:
            orig_move = orig_pick.move_ids.filtered(
                lambda m: m.product_id == move.product_id)[:1]
            if not orig_move:
                continue
            vals = {}
            if not move.amunet_supplier_lot and orig_move.amunet_supplier_lot:
                vals['amunet_supplier_lot'] = orig_move.amunet_supplier_lot
            if not move.amunet_mfg_date and orig_move.amunet_mfg_date:
                vals['amunet_mfg_date'] = orig_move.amunet_mfg_date
            if not move.amunet_exp_date and orig_move.amunet_exp_date:
                vals['amunet_exp_date'] = orig_move.amunet_exp_date
            if vals:
                move.sudo().write(vals)
            # Copiar también a las move_lines (factory_lot_id, fechas estructuradas)
            orig_ml = orig_pick.move_line_ids.filtered(
                lambda l: l.product_id == move.product_id)[:1]
            if orig_ml:
                for ml in move.move_line_ids:
                    ml_vals = {}
                    if not ml.factory_lot_id and orig_ml.factory_lot_id:
                        ml_vals['factory_lot_id'] = orig_ml.factory_lot_id.id
                    if not ml.manufacturing_date and orig_ml.manufacturing_date:
                        ml_vals['manufacturing_date'] = orig_ml.manufacturing_date
                    if not ml.expiration_date and orig_ml.expiration_date:
                        ml_vals['expiration_date'] = orig_ml.expiration_date
                    if ml_vals:
                        ml.sudo().write(ml_vals)

    def action_confirm(self):
        for picking in self.filtered(
            lambda p: p.picking_type_code == 'incoming'
            # Las liberaciones de QC (recepcion de disposicion) ya traen destino
            # Existencias puesto por Calidad; NO re-enrutar a Control de calidad,
            # si no se re-cuarentena un lote ya aprobado.
            and not getattr(p, 'amunet_disposition_qc_id', False)
        ):
            wh = picking.picking_type_id.warehouse_id
            stock_loc = wh.lot_stock_id if wh else None
            qc_loc = wh.wh_qc_stock_loc_id if wh else None
            for move in picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
                # Requiere analisis (flag del producto o de su categoria): va a
                # Control de calidad. Si NO requiere: entra DIRECTO a Existencias
                # en un solo paso, sin pasar por Control de calidad.
                if move.product_id.product_tmpl_id._amunet_effective_requires_quarantine():
                    if qc_loc:
                        move.location_dest_id = qc_loc.id
                elif stock_loc:
                    move.location_dest_id = stock_loc.id

        result = super().action_confirm()

        # amunet_lot genera lot_name en la línea pero no crea el registro stock.lot
        # hasta la validación. Lo creamos aquí para que sea visible en la tabla.
        for picking in self.filtered(lambda p: p.picking_type_code == 'incoming'):
            for line in picking.move_line_ids.filtered(lambda l: l.lot_name and not l.lot_id):
                lot = self.env['stock.lot'].search([
                    ('name', '=', line.lot_name),
                    ('product_id', '=', line.product_id.id),
                ], limit=1)
                if not lot:
                    lot = self.env['stock.lot'].sudo().create({
                        'name': line.lot_name,
                        'product_id': line.product_id.id,
                        'company_id': line.company_id.id,
                    })
                line.lot_id = lot.id

        return result

    def _amunet_check_duplicate_supplier_lots(self):
        """Aviso al validar una recepcion: si el MISMO producto tiene 2 o mas
        lotes Amunet con el MISMO lote de proveedor, probablemente llego de mas
        y se capturo en lotes separados por error (deberia ser UN solo lote).
        Se avisa para que revisen/consoliden antes de validar. Solo se dispara
        cuando el lote de proveedor coincide -> sin falsos positivos si de verdad
        son lotes distintos."""
        Prod = self.env['product.product']
        for p in self.filtered(lambda x: x.picking_type_code == 'incoming'):
            grupos = {}
            for line in p.move_line_ids:
                sup = line.factory_lot_id.name if line.factory_lot_id else False
                if not sup:
                    continue
                key = (line.product_id.id, sup)
                lote = line.lot_id.name or line.lot_name or ''
                grupos.setdefault(key, set()).add(lote)
            dups = {k: v for k, v in grupos.items() if len(v) > 1}
            if dups:
                lineas = []
                for (prod_id, sup), lotes in dups.items():
                    lineas.append('  - %s: lote de proveedor "%s" en %s lotes distintos (%s)'
                                  % (Prod.browse(prod_id).display_name, sup,
                                     len(lotes), ', '.join(sorted(lotes))))
                raise UserError(_(
                    'AVISO — revisa la informacion antes de validar.\n\n'
                    'Hay lotes duplicados con el MISMO lote de proveedor:\n%s\n\n'
                    'Si es el MISMO lote (llego de mas), captura todo en UN solo '
                    'lote (sube la cantidad en la misma linea). Si de verdad son '
                    'lotes distintos del proveedor, deben tener numeros de lote de '
                    'proveedor distintos. Corrige y vuelve a validar.'
                ) % '\n'.join(lineas))

    def _amunet_check_datos_recepcion(self):
        """Bloquea la validación si falta lote de proveedor, fecha de fabricación
        o fecha de caducidad en cualquier línea de la recepción.
        Los pickings de liberación de QC (amunet_disposition_qc_id) se excluyen:
        sus datos ya fueron validados en la recepción original."""
        for p in self.filtered(lambda x: x.picking_type_code == 'incoming'
                               and x.state not in ('done', 'cancel')
                               and not x.amunet_disposition_qc_id):
            faltan = []
            for move in p.move_ids.filtered(lambda m: m.state not in ('done', 'cancel')
                                            and m.product_uom_qty > 0):
                prod = move.product_id.display_name
                if not move.amunet_supplier_lot:
                    faltan.append(f'  • {prod}: falta Lote de proveedor')
                if not move.amunet_mfg_date:
                    faltan.append(f'  • {prod}: falta Fecha de fabricación')
                if not move.amunet_exp_date:
                    faltan.append(f'  • {prod}: falta Fecha de caducidad')
            if faltan:
                raise UserError(_(
                    'Completa los datos de recepción antes de validar.\n\n%s\n\n'
                    'Encuéntralos en las columnas de la tabla de operaciones.'
                ) % '\n'.join(faltan))

    def _amunet_check_expiration_captured(self):
        """Aviso al validar una recepcion: los productos que usan caducidad DEBEN
        tener la caducidad real capturada. Bloquea si esta vacia o si quedo en la
        fecha de recepcion o anterior (caso tipico: se puso la fecha de hoy por
        defecto). Asi Almacen no valida con caducidades erroneas."""
        hoy = fields.Date.context_today(self)
        for p in self.filtered(lambda x: x.picking_type_code == 'incoming'):
            faltan, malas = [], []
            for line in p.move_line_ids:
                if (line.quantity or 0) <= 0:
                    continue
                if not line.product_id.product_tmpl_id.use_expiration_date:
                    continue
                exp = line.expiration_date or (
                    line.lot_id.expiration_date if line.lot_id else False)
                # Si la caducidad se capturo en el movimiento (texto) y aun no se
                # propago a la linea, considerarla para no bloquear en falso.
                mv = line.move_id
                if mv and mv.amunet_exp_date:
                    if mv.amunet_exp_date.strip().upper() == 'VIGENTE':
                        continue  # "vigente" es explícitamente válido
                    parsed = _parse_date(mv.amunet_exp_date)
                    if parsed:
                        exp = parsed
                lote = line.lot_id.name or line.lot_name or 's/l'
                etq = '%s (lote %s)' % (line.product_id.display_name, lote)
                if not exp:
                    faltan.append('  - ' + etq)
                else:
                    exp_d = exp.date() if hasattr(exp, 'date') else exp
                    if exp_d <= hoy:
                        malas.append('  - %s: caducidad %s' % (etq, exp_d))
            partes = []
            if faltan:
                partes.append('SIN caducidad capturada:\n' + '\n'.join(faltan))
            if malas:
                partes.append('Caducidad = fecha de recepcion o anterior '
                              '(captura la real):\n' + '\n'.join(malas))
            if partes:
                raise UserError(_(
                    'AVISO — captura la CADUCIDAD real antes de validar.\n\n%s'
                ) % '\n\n'.join(partes))

    def _amunet_check_inspeccion_entrada(self):
        """Bloquea la validación si la inspección de entrada no está completa.
        ISO 13485 §7.4.3: obligatoria para TODA recepción entrante sin excepción."""
        for p in self.filtered(lambda x: x.picking_type_code == 'incoming'
                               and x.state not in ('done', 'cancel')):
            faltantes = []
            if not p.amunet_crit1:
                faltantes.append('• Empaque íntegro, sin perforaciones ni daños externos')
            if not p.amunet_crit2:
                faltantes.append('• Etiqueta legible con información correcta')
            if not p.amunet_crit3:
                faltantes.append('• Sin daños visibles en el material')
            if not p.amunet_crit4:
                faltantes.append('• Certificado de análisis (si no aplica, selecciona N/A)')
            if not p.amunet_crit5:
                faltantes.append('• Cantidad recibida coincide con lo solicitado')
            if faltantes:
                raise UserError(_(
                    'Completa la Inspección de entrada antes de validar.\n\n'
                    'Faltan los siguientes criterios:\n%s\n\n'
                    'Encuéntralos en la pestaña "Inspección de entrada".'
                ) % '\n'.join(faltantes))

    # ── button_validate: pedir PIN antes de validar ──────────────────────────
    amunet_es_recepcion_equipo = fields.Boolean(
        string='Recepción de equipo de uso interno',
        compute='_compute_amunet_es_recepcion_equipo', store=True)

    @api.depends('move_ids.product_id', 'move_ids.product_uom_qty', 'move_ids.state')
    def _compute_amunet_es_recepcion_equipo(self):
        for p in self:
            moves = p.move_ids.filtered(
                lambda m: m.state != 'cancel' and m.product_uom_qty > 0)
            p.amunet_es_recepcion_equipo = bool(moves) and all(
                m.product_id.default_code == 'EQUIPO-USO-INTERNO' for m in moves)

    def _amunet_es_recepcion_equipo(self):
        """True si la recepcion es de un equipo de uso interno (producto
        generico EQUIPO-USO-INTERNO). Estos NO llevan lote de proveedor,
        caducidad, inspeccion ni cuarentena de MP: van al flujo de Validacion.
        SI conservan el PIN de Almacen al validar."""
        self.ensure_one()
        return self.amunet_es_recepcion_equipo

    def _amunet_realinear_destino_equipo(self):
        """El equipo se queda en AMP/Entrada (no pasa a Existencias): alinea el
        destino de los movimientos al del encabezado de la recepcion."""
        self.ensure_one()
        dest = self.location_dest_id
        if not dest:
            return
        moves = self.move_ids.filtered(lambda m: m.state not in ('done', 'cancel'))
        if moves:
            moves.write({'location_dest_id': dest.id})
        if self.move_line_ids:
            self.move_line_ids.write({'location_dest_id': dest.id})

    def button_validate(self):
        # Recepcion de equipo de uso interno: exenta de los datos/caducidad/
        # inspeccion/cuarentena de MP, PERO conserva el PIN de Almacen. La
        # solicitud de ingreso la genera despues el modulo de Validacion.
        es_equipo = bool(self) and all(
            p.amunet_es_recepcion_equipo for p in self)
        if es_equipo:
            # El equipo se queda en AMP/Entrada, no en Existencias.
            for p in self.filtered(lambda x: x.state not in ('done', 'cancel')):
                p._amunet_realinear_destino_equipo()
        if not es_equipo:
            self._amunet_check_duplicate_supplier_lots()
            self._amunet_check_datos_recepcion()
            self._amunet_check_expiration_captured()
            # La inspeccion de entrada NO bloquea la recepcion (alineado a
            # produccion, criterio de Fernando): el control de aceptacion va en
            # la LIBERACION de Calidad, no al recibir. Si faltan los criterios,
            # se agenda actividad a Calidad (ver rama _skip_pin_wizard abajo).
            # Se conserva _amunet_check_datos_recepcion (lote proveedor + fechas)
            # por trazabilidad.
        if self.env.context.get('_skip_pin_wizard'):
            res = super().button_validate()
            if not es_equipo:
                for p in self.filtered(lambda p: p.picking_type_code == 'incoming'
                                       and p.state == 'done'):
                    if not all([p.amunet_crit1, p.amunet_crit2, p.amunet_crit3,
                                p.amunet_crit4, p.amunet_crit5]):
                        p._amunet_notify_quality_pending()
                    # Lotes de productos sin cuarentena → liberar automáticamente
                    for line in p.move_line_ids:
                        if (line.lot_id
                                and not line.product_id.product_tmpl_id._amunet_effective_requires_quarantine()
                                and line.lot_id.amunet_lot_release_state != 'released'):
                            line.lot_id.sudo().write({'amunet_lot_release_state': 'released'})
            return res
        incoming = self.filtered(lambda p: p.picking_type_code == 'incoming'
                                 and p.state not in ('done', 'cancel'))
        if not incoming:
            return super().button_validate()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirmar recepcion',
            'res_model': 'amunet.recepcion.pin.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_picking_id': self.id},
        }

    def _amunet_notify_quality_pending(self):
        """Agenda una actividad a Calidad cuando la recepcion se valida con
        criterios de aceptacion pendientes (asignar criterios + inspeccionar)."""
        self.ensure_one()
        group = (self.env.ref('amunet_quality.group_quality_supervisor',
                              raise_if_not_found=False)
                 or self.env.ref('amunet_quality.group_quality_user',
                                 raise_if_not_found=False))
        qc_user = group.user_ids[:1] if (group and group.user_ids) else self.env.user
        codes = [c for c in self.move_ids.product_id.mapped('default_code') if c]
        prods = ', '.join(codes) or ', '.join(self.move_ids.product_id.mapped('display_name'))
        summary = _('Asignar criterios de aceptacion e inspeccion - recepcion %s') % self.name
        note = _('La recepcion %s se valido con criterios de aceptacion pendientes. '
                 'Producto(s): %s. Calidad debe asignar criterios/especificaciones e '
                 'inspeccionar antes de liberar de cuarentena.') % (self.name, prods)
        try:
            self.activity_schedule('mail.mail_activity_data_todo',
                                   user_id=qc_user.id, summary=summary, note=note)
        except Exception:
            self.message_post(body=note)

    def action_open_serial_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Números de serie del equipo',
            'res_model': 'amunet.reception.serial.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_picking_id': self.id},
        }

    def _amunet_crear_traslado_distribucion(self):
        """Cuando una liberación de QC se valida y el producto es de categoría
        Distribución/*, crea una recepción en APT para que Luis confirme físicamente
        que recibió el equipo o material."""
        self.ensure_one()

        cat_raiz = self.env['product.category'].search(
            [('name', '=', 'Distribución')], limit=1)
        if not cat_raiz:
            return
        cat_ids = self.env['product.category'].search(
            [('id', 'child_of', cat_raiz.id)]).ids

        lines = self.move_line_ids.filtered(
            lambda l: l.product_id.categ_id.id in cat_ids and (l.quantity or 0) > 0
        )
        if not lines:
            return

        loc_apt = self.env['stock.location'].search([
            ('name', '=', 'Existencias_Distribución'),
            ('usage', '=', 'internal'),
        ], limit=1)
        if not loc_apt:
            _logger.warning(
                'amunet_recepcion: no se encontró Existencias_Distribución; '
                'traslado automático no creado para picking %s', self.name)
            return

        # Usar el tipo Traslados internos de APT (no Recepciones) para evitar
        # que la ruta multi-paso de APT desvíe el material a QC intermedio.
        # El material ya pasó QC en AMP; va directo a Existencias_Distribución.
        wh_apt = self.env['stock.warehouse'].search(
            [('code', '=', 'APT')], limit=1)
        pt = wh_apt.int_type_id if wh_apt else False
        if not pt:
            _logger.warning(
                'amunet_recepcion: no se encontró almacén APT o su tipo interno; '
                'traslado automático no creado para picking %s', self.name)
            return

        loc_src = lines[0].location_dest_id  # AMP/Existencias

        # Cantidad real aprobada: suma de quants en ubicaciones internas.
        # Si hubo split antes de la liberación, el picking de QC mueve la cantidad
        # original (ej. 5) pero solo existían 3 en QC → queda +5 en Existencias
        # y -2 en QC. La suma interna 5 + (-2) = 3, que es la cantidad correcta.
        def _qty_real(line):
            if not line.lot_id:
                return line.quantity
            quants = self.env['stock.quant'].search([
                ('product_id', '=', line.product_id.id),
                ('lot_id', '=', line.lot_id.id),
                ('location_id.usage', '=', 'internal'),
            ])
            total = sum(quants.mapped('quantity'))
            return total if total > 0 else line.quantity

        move_vals = [(0, 0, {
            'product_id': l.product_id.id,
            'product_uom_qty': _qty_real(l),
            'product_uom': l.product_id.uom_id.id,
            'location_id': loc_src.id,
            'location_dest_id': loc_apt.id,
        }) for l in lines]

        traslado = self.env['stock.picking'].sudo().create({
            'picking_type_id': pt.id,
            'location_id': loc_src.id,
            'location_dest_id': loc_apt.id,
            'origin': 'Distribución desde QC: ' + self.name,
            'move_ids': move_vals,
        })
        traslado.action_confirm()
        # Forzar destino directo a Existencias_Distribución en todos los movimientos,
        # evitando que la ruta multi-paso de APT desvíe a QC intermedio.
        traslado.move_ids.write({'location_dest_id': loc_apt.id})
        traslado.action_assign()

        # Asignar lote y datos de proveedor en las líneas del traslado
        # y construir resumen para la nota de Luis.
        # Si la liberación de QC no tiene los datos del proveedor (factory_lot,
        # fechas), los buscamos en la recepción original como respaldo.
        qc = self.amunet_disposition_qc_id
        orig_ml_map = {}
        if qc and qc.picking_id:
            for oml in qc.picking_id.move_line_ids:
                orig_ml_map[oml.product_id.id] = oml

        resumen_lineas = []
        for line in lines:
            if not line.lot_id:
                continue
            ml = traslado.move_line_ids.filtered(
                lambda ml, p=line.product_id: ml.product_id == p
            )[:1]
            if ml:
                orig = orig_ml_map.get(line.product_id.id)
                factory_lot = line.factory_lot_id or (orig.factory_lot_id if orig else False)
                mfg_date = line.manufacturing_date or (orig.manufacturing_date if orig else False)
                exp_date = line.expiration_date or (orig.expiration_date if orig else False)
                ml.write({
                    'lot_id': line.lot_id.id,
                    'quantity': line.quantity,
                    'factory_lot_id': factory_lot.id if factory_lot else False,
                    'manufacturing_date': mfg_date,
                    'expiration_date': exp_date,
                })
                num_serie = factory_lot.name if factory_lot else 'sin número'
                resumen_lineas.append(
                    f'<li>{line.product_id.display_name} — '
                    f'Lote Amunet: <b>{line.lot_id.name}</b> | '
                    f'No. serie/lote proveedor: <b>{num_serie}</b> | '
                    f'Cantidad: <b>{int(line.quantity)}</b></li>'
                )

        detalle = '<ul>' + ''.join(resumen_lineas) + '</ul>' if resumen_lineas else ''

        # Poner el resumen también en la nota interna del traslado para que
        # Luis lo vea al abrir el picking sin necesidad de entrar al lote
        traslado.sudo().write({'note': (
            f'Material liberado por Calidad (origen: {self.name}).\n'
            f'Verifica físicamente cada artículo antes de validar.\n\n'
            + '\n'.join(
                f'- {line.product_id.display_name}: '
                f'Lote {line.lot_id.name} | Serie proveedor: {line.factory_lot_id.name if line.factory_lot_id else "sin número"} | Cant: {int(line.quantity)}'
                for line in lines if line.lot_id
            )
        )})

        # Notificar a Luis con una actividad para que confirme recepción física
        luis = self.env['res.users'].search(
            [('login', '=', 'almacen2@amunet.com.mx')], limit=1)
        if luis:
            traslado.sudo().activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=luis.id,
                summary='Confirmar recepción de equipo/cristalería',
                note=(
                    f'Calidad liberó material de Distribución desde <b>{self.name}</b>.<br/>'
                    f'Verifica físicamente cada artículo y valida la recepción:<br/>'
                    f'{detalle}'
                ),
            )

        self.message_post(
            body=(
                f'Recepción en APT/Distribución generada: <b>{traslado.name}</b>. '
                f'Luis (APT) recibirá aviso para confirmar.'
            ),
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )

    def _action_done(self):
        res = super()._action_done()
        # Liberaciones de QC con productos de categoría Distribución/* →
        # crear traslado automático a APT/Existencias_Distribución
        for picking in self.filtered(
            lambda p: p.state == 'done' and p.amunet_disposition_qc_id
        ):
            picking._amunet_crear_traslado_distribucion()
        for picking in self.filtered(
            lambda p: p.picking_type_code == 'incoming' and p.amunet_con_observaciones
        ):
            criterios = {
                'Empaque íntegro': picking.amunet_crit1,
                'Etiqueta legible': picking.amunet_crit2,
                'Sin daños visibles': picking.amunet_crit3,
                'Certificado de análisis': picking.amunet_crit4,
                'Cantidad correcta': picking.amunet_crit5,
            }
            fallidos = [nombre for nombre, val in criterios.items() if val == 'nok']
            if not fallidos:
                continue
            detalle = ', '.join(fallidos)
            obs = picking.amunet_crit_obs or '(sin observaciones adicionales)'
            msg = (
                f'⚠️ <b>Material recibido con observaciones — requiere revisión de Calidad</b><br/>'
                f'Criterios que no cumplen: <b>{detalle}</b><br/>'
                f'Observaciones: {obs}<br/>'
                f'Recepción: {picking.name} | Recibió: {picking.amunet_receptor_id.name or "—"}'
            )
            lot_ids = picking.move_line_ids.mapped('lot_id').filtered(lambda l: l.id)
            qcs = self.env['amunet.quality.check'].search([
                ('lot_id', 'in', lot_ids.ids),
                ('state', 'not in', ('done',)),
            ])
            for qc in qcs:
                qc.message_post(body=msg, message_type='notification',
                                subtype_xmlid='mail.mt_note')
        return res
