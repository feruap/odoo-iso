# -*- coding: utf-8 -*-
"""Movimiento de inventario de la entrega de producto terminado al almacen PT.

Lo que faltaba: hasta ahora la entrega y su recepcion eran solo un registro de
custodia con doble firma, pero NO movian inventario. El papel decia que el
almacen habia recibido y Odoo seguia creyendo que el material estaba en
produccion. Ese descuadre es el que alimenta los fantasmas de inventario.

Recorrido fisico:

    APT/Almacen Temporal PT   (donde aterriza lo que se fabrica)
             |  entrega firmada con PIN -> se mueve de inmediato
             v
    APT/Entrada               (custodia del almacen, todavia NO es existencia)
             |  el almacenista valida el "Ingreso a PT"
             v
    APT/Existencias_Presentacion 1 pieza

Si el almacenista RECHAZA (conto distinto), el material regresa a Temporal PT y
Produccion repite la entrega. No se acepta a medias: se aclara primero.

Las ubicaciones se resuelven por NOMBRE y se pueden reconfigurar con parametros
del sistema, porque en esta instalacion se crearon a mano y no tienen
identificador de modulo.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Parametros para reconfigurar sin tocar codigo
P_ORIGEN = 'amunet_woocommerce.entrega_pt.ubicacion_origen'
P_ENTRADA = 'amunet_woocommerce.entrega_pt.ubicacion_entrada'
P_EXISTENCIAS = 'amunet_woocommerce.entrega_pt.ubicacion_existencias'

D_ORIGEN = 'APT/Almacén Temporal PT'
D_ENTRADA = 'APT/Entrada'
D_EXISTENCIAS = 'APT/Existencias_Presentación 1 pieza'


class AmunetEntregaPtStock(models.Model):
    _inherit = 'amunet.entrega.pt'

    picking_ingreso_id = fields.Many2one(
        'stock.picking',
        string='Ingreso a PT',
        readonly=True, copy=False,
        help='Documento que el almacenista valida para que el material entre a '
             'existencias.')

    # ------------------------------------------------------------------
    # Ubicaciones
    # ------------------------------------------------------------------
    @api.model
    def _entrega_pt_ubicacion(self, parametro, nombre_por_defecto):
        """Resuelve una ubicacion por parametro o, si no, por nombre."""
        # active_test=False a proposito: APT/Entrada esta ARCHIVADA en algunas
        # instalaciones y una busqueda normal no la ve. Sin esto el flujo falla
        # con "no se encontro la ubicacion" aunque exista. Si esta archivada se
        # reactiva: es una ubicacion operativa del recorrido.
        Loc = self.env['stock.location'].sudo().with_context(active_test=False)
        valor = self.env['ir.config_parameter'].sudo().get_param(parametro)
        if valor:
            loc = Loc.browse(int(valor)) if valor.isdigit() else Loc.search(
                [('complete_name', '=', valor)], limit=1)
            if loc.exists():
                return loc
        loc = Loc.search([('complete_name', '=', nombre_por_defecto)], limit=1)
        if loc and not loc.active:
            loc.active = True
        if not loc:
            raise UserError(_(
                'No se encontro la ubicacion "%(nombre)s".\n\n'
                'Si en este almacen se llama de otra forma, configurala en el '
                'parametro del sistema %(param)s.'
            ) % {'nombre': nombre_por_defecto, 'param': parametro})
        return loc

    @api.model
    def _entrega_pt_origen(self):
        return self._entrega_pt_ubicacion(P_ORIGEN, D_ORIGEN)

    @api.model
    def _entrega_pt_entrada(self):
        return self._entrega_pt_ubicacion(P_ENTRADA, D_ENTRADA)

    @api.model
    def _entrega_pt_existencias(self):
        return self._entrega_pt_ubicacion(P_EXISTENCIAS, D_EXISTENCIAS)

    # ------------------------------------------------------------------
    # Tipo de operacion
    # ------------------------------------------------------------------
    @api.model
    def _entrega_pt_picking_type(self):
        """Tipo de operacion propio del ingreso a PT.

        Se crea uno dedicado en lugar de reusar 'Almacenamiento' para que el
        documento se llame por su nombre y el almacenista lo distinga de un
        traslado interno cualquiera. Se resuelve o crea al vuelo porque los
        almacenes de esta instalacion se hicieron a mano.
        """
        PT = self.env['stock.picking.type'].sudo()
        entrada = self._entrega_pt_entrada()
        existencias = self._entrega_pt_existencias()
        almacen = existencias.warehouse_id or entrada.warehouse_id
        tipo = PT.search([
            ('code', '=', 'internal'),
            ('sequence_code', '=', 'APTIN'),
            ('warehouse_id', '=', almacen.id),
        ], limit=1)
        if tipo:
            return tipo
        secuencia = self.env['ir.sequence'].sudo().search(
            [('code', '=', 'amunet.woo.ingreso.pt')], limit=1)
        if not secuencia:
            secuencia = self.env['ir.sequence'].sudo().create({
                'name': 'Ingreso a Almacen de PT',
                'code': 'amunet.woo.ingreso.pt',
                'prefix': 'APT/IN/',
                'padding': 5,
                'company_id': False,
            })
        return PT.create({
            'name': 'Ingreso a PT',
            'sequence_code': 'APTIN',
            'code': 'internal',
            'sequence_id': secuencia.id,
            'warehouse_id': almacen.id,
            'default_location_src_id': entrada.id,
            'default_location_dest_id': existencias.id,
            'use_existing_lots': True,
            'use_create_lots': False,
        })

    # ------------------------------------------------------------------
    # Cuanto se puede entregar
    # ------------------------------------------------------------------
    @api.model
    def _entrega_pt_pendiente(self, lot, production=None):
        """Piezas del lote que se pueden entregar: lo que hay en Temporal PT.

        Con movimiento de inventario real, la verdad es lo que esta fisicamente
        en el origen. Se descuenta lo ya entregado y todavia sin validar, que
        ya salio de Temporal pero aun no es existencia.
        """
        if not lot:
            return 0.0
        origen = self._entrega_pt_origen()
        disponible = self.env['stock.quant'].sudo()._get_available_quantity(
            lot.product_id, origen, lot_id=lot)
        if production is not None and production:
            # Y lo que la orden todavia debe sacar. Mientras la orden esta en
            # curso, esas piezas aun no existen -Odoo no crea el terminado
            # hasta cerrarla- pero SI se pueden entregar: la entrega las
            # materializa (ver _entrega_pt_materializar). Sin esto la pantalla
            # decia "no hay piezas pendientes" con 400 anotadas en la orden.
            # OJO: se suma product_uom_qty COMPLETO de los movimientos que no
            # estan hechos. No se le resta 'quantity': ese campo viene
            # prellenado con la cantidad a producir aunque no se haya producido
            # nada, asi que restarlo daba siempre 0 y la pantalla se negaba a
            # abrir. Lo ya materializado vive en movimientos 'done', que quedan
            # fuera de este filtro y se cuentan por existencia fisica arriba:
            # no hay doble conteo.
            por_producir = sum(
                m.product_uom_qty
                for m in production.move_finished_ids
                if m.product_id == lot.product_id
                and m.state not in ('done', 'cancel'))
            disponible += max(0.0, por_producir)
        return max(0.0, disponible)

    # ------------------------------------------------------------------
    # Materializacion de las piezas que se entregan
    # ------------------------------------------------------------------
    def _entrega_pt_materializar(self):
        """Hace que existan de verdad las piezas que se van a entregar.

        El problema que resuelve: Produccion entrega ANTES de cerrar la orden,
        pero Odoo no crea el producto terminado hasta que la orden se marca
        producida. Mientras esta en curso la cantidad esta anotada y el
        movimiento en 'assigned', pero no hay una sola pieza en el almacen.

        Se marca hecho SOLO el pedazo que se entrega del movimiento de salida.
        Odoo parte el movimiento solo (_create_backorder) y deja el resto como
        un movimiento nuevo de la MISMA orden, asi que:
          - el folio NO cambia (eso lo haria _split_productions, que no se usa)
          - NO nace una orden hija
          - qty_produced sube solo, porque se calcula sumando los movimientos
            de salida ya marcados como hechos

        LOS INSUMOS NO SE TOCAN. Es el candado de todo esto: la rutina completa
        de produccion (_post_inventory) CANCELA los insumos que no esten
        surtidos, y hoy la mayoria de las ordenes en curso tienen material sin
        surtir. Entregar producto terminado no debe consumir ni cancelar
        material: eso sigue pasando al cerrar la orden, donde siempre paso.
        """
        self.ensure_one()
        mo = self.production_id
        if not mo:
            return False
        pendiente = mo.move_finished_ids.filtered(
            lambda m: m.product_id == self.product_id
            and m.state not in ('done', 'cancel'))
        if not pendiente:
            # Ya se produjo por la via normal; no hay nada que materializar.
            return False
        move = pendiente[0]
        por_hacer = min(self.quantity_delivered, move.product_uom_qty)
        if por_hacer <= 0:
            return False

        move.move_line_ids.unlink()
        self.env['stock.move.line'].sudo().create({
            'move_id': move.id,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_id.uom_id.id,
            'lot_id': self.lot_id.id,
            'quantity': por_hacer,
            'location_id': move.location_id.id,
            'location_dest_id': move.location_dest_id.id,
        })
        move.picked = True
        # cancel_backorder=False: el sobrante se conserva como movimiento
        # nuevo de la misma orden, que es justo lo que se quiere.
        move.sudo().with_context(skip_mo_check=True)._action_done(
            cancel_backorder=False)
        return move

    # ------------------------------------------------------------------
    # Movimientos
    # ------------------------------------------------------------------
    def _entrega_pt_mover(self, origen, destino, referencia):
        """Mueve las piezas de la entrega entre dos ubicaciones, ya validado."""
        self.ensure_one()
        Picking = self.env['stock.picking'].sudo()
        picking = Picking.create({
            'picking_type_id': self._entrega_pt_picking_type().id,
            'location_id': origen.id,
            'location_dest_id': destino.id,
            'origin': referencia,
            'company_id': self.company_id.id,
            'move_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'product_uom_qty': self.quantity_delivered,
                'product_uom': self.product_id.uom_id.id,
                'location_id': origen.id,
                'location_dest_id': destino.id,
                'company_id': self.company_id.id,
            })],
        })
        picking.action_confirm()
        # La linea se ESCRIBE, no se espera de la reserva automatica.
        #
        # Por que: las piezas que se entregan acaban de materializarse en esta
        # misma transaccion (_entrega_pt_materializar). El motor de reserva de
        # Odoo no las ve todavia: _update_reserved_quantity devuelve 0 aunque el
        # quant tenga las 200 piezas libres, sin dueno ni paquete. El picking se
        # quedaba en 'confirmed' sin lineas y button_validate reventaba con
        # "no has puesto cantidades".
        #
        # Escribir la linea es ademas lo correcto aqui: el lote no es una
        # eleccion del motor, es EL lote que se esta entregando, y es el dato
        # que arrastra fecha de fabricacion y caducidad al almacen.
        picking.move_ids.move_line_ids.unlink()
        for move in picking.move_ids:
            self.env['stock.move.line'].sudo().create({
                'move_id': move.id,
                'picking_id': picking.id,
                'product_id': self.product_id.id,
                'product_uom_id': self.product_id.uom_id.id,
                'lot_id': self.lot_id.id,
                'quantity': self.quantity_delivered,
                'location_id': origen.id,
                'location_dest_id': destino.id,
            })
        picking.move_ids.picked = True
        # skip_expired: Odoo abre un wizard de confirmacion cuando el lote esta
        # vencido o por vencer. Aqui estorba y es peligroso: el wizard NO se
        # puede atender desde este flujo, asi que button_validate devolvia una
        # accion, el documento se quedaba en 'assigned' EN SILENCIO y el
        # material nunca se movia. Ese descuadre mudo es justo el fantasma de
        # inventario que este modulo vino a eliminar.
        # El aviso no se pierde: la pantalla de entrega muestra la caducidad y
        # exige confirmarla contra el producto fisico antes de firmar, que es un
        # control mas claro que el generico de Odoo.
        picking.with_context(skip_expired=True).button_validate()
        return picking

    def _entrega_pt_generar_ingreso(self):
        """Crea el documento que el almacenista debe validar.

        Se deja SIN validar a proposito: mientras no lo valide, el material
        esta en APT/Entrada -a la vista, bajo su custodia- pero todavia no es
        existencia vendible.
        """
        self.ensure_one()
        entrada = self._entrega_pt_entrada()
        existencias = self._entrega_pt_existencias()
        # Si Calidad YA aprobo el analisis, el ingreso se marca como entrega de
        # PT para que al validarlo corra el candado de siempre
        # (amunet_production._amunet_liberar_lotes_entrega): libera el lote a
        # nombre del Responsable Sanitario. Se reusa ese mecanismo en vez de
        # duplicarlo.
        #
        # Si el analisis NO esta aprobado, NO se marca: durante el periodo de
        # gracia se puede entregar sin liberacion, y liberar material que
        # Calidad no ha aprobado seria justo lo contrario de lo que cuida ese
        # candado.
        aprobado = getattr(
            self.production_id, 'quality_analysis_status', False) == 'approved'
        picking = self.env['stock.picking'].sudo().create({
            'picking_type_id': self._entrega_pt_picking_type().id,
            'location_id': entrada.id,
            'location_dest_id': existencias.id,
            'origin': _('Entrega de PT %s') % (self.production_id.name or ''),
            'company_id': self.company_id.id,
            'amunet_es_entrega_pt': aprobado,
            'amunet_entrega_mo_id': self.production_id.id,
            'move_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'product_uom_qty': self.quantity_delivered,
                'product_uom': self.product_id.uom_id.id,
                'location_id': entrada.id,
                'location_dest_id': existencias.id,
                'company_id': self.company_id.id,
            })],
        })
        picking.action_confirm()
        # Misma razon que en _entrega_pt_mover: el material acaba de llegar a
        # APT/Entrada en esta misma transaccion y la reserva automatica no lo
        # ve. La linea se escribe con el lote exacto que se entrego.
        picking.move_ids.move_line_ids.unlink()
        for move in picking.move_ids:
            self.env['stock.move.line'].sudo().create({
                'move_id': move.id,
                'picking_id': picking.id,
                'product_id': self.product_id.id,
                'product_uom_id': self.product_id.uom_id.id,
                'lot_id': self.lot_id.id,
                # Lo que Produccion entrego: queda escrito, de solo lectura.
                'qty_demanded': self.quantity_delivered,
                # Lo que el almacen cuenta: se deja en 0 A PROPOSITO. Quien
                # recibe escribe lo que de verdad tiene enfrente; si viniera
                # prellenado, validar seria darle a un boton sin contar.
                'quantity': 0.0,
                'location_id': entrada.id,
                'location_dest_id': existencias.id,
            })
        self.picking_ingreso_id = picking.id
        return picking

    # ------------------------------------------------------------------
    # Validacion y rechazo del almacenista
    # ------------------------------------------------------------------
    def action_entrega_pt_recibir(self):
        """Abre la pantalla que pregunta cuantas piezas se estan recibiendo."""
        self.ensure_one()
        return self.env['amunet.recibir.pt.wizard'].abrir_para(self)

    def action_entrega_pt_validar(self):
        """El almacen acepta: el material entra a existencias."""
        for rec in self:
            if not rec.picking_ingreso_id:
                raise UserError(_(
                    'Esta entrega no tiene documento de ingreso a PT.'))
            if rec.picking_ingreso_id.state == 'done':
                raise UserError(_('El ingreso %s ya estaba validado.')
                                % rec.picking_ingreso_id.name)
            picking = rec.picking_ingreso_id.sudo()
            # Se valida CONTRA LO QUE CONTO EL ALMACEN, no contra lo que dijo
            # Produccion. Antes esta linea sobreescribia el conteo con la
            # cantidad entregada, asi que daba igual lo que se capturara.
            contado = sum(picking.move_ids.move_line_ids.mapped('quantity'))
            if not contado:
                raise UserError(_(
                    'Escribe en "Cant. real" cuantas piezas estas recibiendo '
                    'antes de validar.\n\n'
                    'Produccion entrego %(entregado)s pza(s) del lote '
                    '%(lote)s.'
                ) % {'entregado': rec.quantity_delivered,
                     'lote': rec.lot_id.name or ''})
            if abs(contado - rec.quantity_delivered) > 0.0001:
                # La regla la fijo Mery: no se acepta a medias. Si el conteo no
                # cuadra se rechaza y Produccion aclara, para que no quede un
                # faltante sin explicacion dentro del almacen.
                raise UserError(_(
                    'Estas recibiendo %(contado)s pza(s) pero Produccion '
                    'entrego %(entregado)s del lote %(lote)s.\n\n'
                    'Una entrega no se acepta a medias. Si el conteo no cuadra, '
                    'usa RECHAZAR: el material regresa completo a Produccion, '
                    'ellos aclaran la diferencia y vuelven a entregar.'
                ) % {'contado': contado, 'entregado': rec.quantity_delivered,
                     'lote': rec.lot_id.name or ''})
            picking.move_ids.picked = True
            picking.with_context(skip_expired=True).button_validate()
            # La entrega se cierra. Sin esto quedaba en 'por recibir' aunque el
            # material ya estuviera en existencias: los botones seguian a la
            # vista y no habia forma de saber que ya se habia atendido.
            rec.state = 'recibida'
            rec.message_post(body=_(
                'Ingreso a PT validado por <b>%(quien)s</b>: %(qty)s pza(s) del '
                'lote <b>%(lote)s</b> entraron a existencias.',
                quien=self.env.user.display_name, qty=rec.quantity_delivered,
                lote=rec.lot_id.name))
        return True

    def action_entrega_pt_rechazar(self):
        """El almacen conto distinto: el material REGRESA a produccion.

        No se acepta a medias. Produccion aclara la diferencia y vuelve a
        entregar. Se cancela el ingreso pendiente y se devuelve el material de
        APT/Entrada a Temporal PT, para que el inventario refleje donde esta de
        verdad.
        """
        for rec in self:
            if rec.picking_ingreso_id and rec.picking_ingreso_id.state != 'done':
                rec.picking_ingreso_id.sudo().action_cancel()
            rec._entrega_pt_mover(
                rec._entrega_pt_entrada(), rec._entrega_pt_origen(),
                _('Rechazo de entrega %s') % (rec.production_id.name or ''))
            rec.state = 'rechazada'
            rec.message_post(body=_(
                'Entrega RECHAZADA por <b>%(quien)s</b>. El material regreso a '
                '%(origen)s; Produccion debe aclarar la diferencia y volver a '
                'entregar.',
                quien=self.env.user.display_name,
                origen=rec._entrega_pt_origen().complete_name))
            rec._entrega_pt_avisar_rechazo()
        return True

    def _entrega_pt_avisar_rechazo(self):
        """Le avisa a Produccion que su entrega no paso.

        La nota del rechazo quedaba solo en el historial de la ENTREGA, que
        Produccion no mira: ellos viven en su orden de fabricacion. Sin este
        aviso el material regresaba a Temporal PT y nadie se enteraba hasta que
        alguien preguntara. Lo detecto Mery el 2026-09-02.

        Se avisa en los dos lugares donde si van a verlo:
          - en el historial de SU ORDEN, que es la pantalla que tienen abierta;
          - como actividad pendiente para quien entrego, para que le salga en
            su lista de tareas y no se le pase.
        """
        self.ensure_one()
        mo = self.production_id
        if not mo:
            return
        cuerpo = _(
            'El almacen RECHAZO la entrega <b>%(entrega)s</b>: '
            '%(qty)s pza(s) del lote <b>%(lote)s</b>.<br/><br/>'
            'Rechazada por <b>%(quien)s</b>. El material ya regreso completo a '
            '<b>%(origen)s</b>, no se perdio nada.<br/><br/>'
            '<b>Que sigue:</b> revisen la diferencia con el almacen -normalmente '
            'es que el conteo no coincidio- y vuelvan a entregar con el boton '
            '"Entrega de PT" de esta misma orden.',
            entrega=self.name or '',
            qty=int(self.quantity_delivered),
            lote=self.lot_id.name or '',
            quien=self.env.user.display_name,
            origen=self._entrega_pt_origen().complete_name,
        )
        mo.sudo().message_post(body=cuerpo)
        # Y una tarea para quien entrego, que es quien tiene que volver a
        # hacerlo. Si no se sabe quien fue, se le deja al responsable de la orden.
        responsable = self.delivered_by or mo.user_id
        if responsable:
            mo.sudo().activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('Volver a entregar a PT: el almacen rechazo %s')
                        % (self.name or ''),
                note=cuerpo,
                user_id=responsable.id,
            )
