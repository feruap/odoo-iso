# -*- coding: utf-8 -*-
import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

RESPONSABLE_SANITARIO_LOGIN = 'r.sanitario@amunet.com.mx'


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    amunet_es_entrega_pt = fields.Boolean(
        string='Entrega de producto terminado', default=False, copy=False,
        help='Traslado del producto terminado del Almacen Temporal PT (cancha '
             'de Calidad) a Existencias. Se genera al APROBAR el analisis del '
             'PT; al validarlo (Almacen, cuando Produccion entrega), se LIBERA '
             'el lote y pasa a Posproduccion.')
    amunet_entrega_mo_id = fields.Many2one(
        'mrp.production', string='MO de la entrega PT', copy=False, index=True)

    def _action_done(self):
        """Override Amunet:
        Cuando el almacenista valida un picking de surtido de
        materiales (origen = nombre de una MO), cerrar
        automaticamente la workorder de la estacion 'AMP' (Almacen
        Materia Prima) de esa MO si esta pendiente.

        Asi el supervisor de produccion ve en la MO que la actividad
        'Surtido de materiales' ya esta hecha, sin que el almacenista
        tenga que entrar a la MO a marcarla.
        """
        res = super()._action_done()
        for picking in self:
            picking._amunet_auto_close_supply_workorder()
        for picking in self.filtered(lambda p: p.amunet_es_entrega_pt):
            picking._amunet_liberar_lotes_entrega()
        return res

    def _amunet_liberar_lotes_entrega(self):
        """Al validar la ENTREGA de PT (Almacen), libera los lotes movidos a
        Existencias a nombre del Responsable Sanitario. El analisis ya fue
        aprobado por Calidad (es la condicion para que exista esta entrega)."""
        self.ensure_one()
        rs = self.env['res.users'].sudo().search(
            [('login', '=', RESPONSABLE_SANITARIO_LOGIN)], limit=1)
        Lot = self.env['stock.lot']
        if 'amunet_lot_release_state' not in Lot._fields:
            return
        lots = self.move_line_ids.mapped('lot_id').filtered(
            lambda l: l.amunet_lot_release_state != 'released')
        origen = self.amunet_entrega_mo_id.name or self.origin or self.name
        for lot in lots:
            vals = {
                'amunet_lot_release_state': 'released',
                'amunet_lot_released_date': fields.Datetime.now(),
                'amunet_lot_release_notes': (
                    'Liberado al validar la entrega de producto terminado de '
                    '%s (Calidad aprobo el analisis).') % origen,
            }
            if rs:
                vals['amunet_lot_released_by_id'] = rs.id
            try:
                lot.sudo().with_context(
                    skip_lot_release_lock=True).write(vals)
            except Exception as exc:
                _logger.warning(
                    'No se pudo liberar el lote %s en la entrega %s: %s',
                    lot.name, self.name, exc)

    def _amunet_auto_close_supply_workorder(self):
        """Busca la MO asociada al picking via 'origin' y cierra la
        workorder de AMP si esta pending/ready/progress.
        """
        self.ensure_one()
        if not self.origin:
            return
        mo = self.env['mrp.production'].sudo().search([
            ('name', '=', self.origin),
        ], limit=1)
        if not mo:
            return
        wo_amp = mo.workorder_ids.filtered(
            lambda w: w.workcenter_id.code == 'AMP'
            and w.state not in ('done', 'cancel')
        )
        for wo in wo_amp:
            try:
                if wo.state in ('pending', 'waiting', 'ready'):
                    wo.sudo().button_start()
                wo.sudo().button_finish()
                mo.message_post(body=(
                    'Workorder "%s" (estacion AMP) cerrada '
                    'automaticamente al validar el picking %s.'
                ) % (wo.name, self.name))
                _logger.info(
                    'Auto-cerrada workorder AMP %s al validar '
                    'picking %s', wo.id, self.name)
            except Exception as exc:
                _logger.warning(
                    'No se pudo auto-cerrar workorder AMP %s tras '
                    'validar picking %s: %s',
                    wo.id, self.name, exc)


class StockPickingCuarentena(models.Model):
    """Cuarentena de ingreso: sellar al entrar, no dejar salir antes de tiempo.

    Va en una clase aparte para que se lea de corrido lo que hace la cuarentena
    sin mezclarlo con la entrega de PT, que es otro asunto.

    Solo actua sobre productos con 'amunet_dias_cuarentena' > 0. Para todo lo
    demas -- el catalogo entero menos los 12 viales -- este codigo se sale a la
    primera linea y nada cambia.
    """
    _inherit = 'stock.picking'

    def _amunet_es_ubicacion_cuarentena(self, ubicacion):
        return bool(ubicacion) and 'Control de calidad' in (
            ubicacion.complete_name or '')

    def button_validate(self):
        # --- SALIDA: no se saca de cuarentena antes de tiempo ---------------
        #
        # Antes de esto, al cerrar la orden nacia solo el traslado
        # 'Control de calidad -> Existencias' en estado 'assigned': Almacen lo
        # podia validar el mismo dia y el vial salia a existencias sin reposo
        # y sin analisis. La cadena fisica existia; el control, no.
        for picking in self:
            if not picking._amunet_es_ubicacion_cuarentena(picking.location_id):
                continue
            if picking._amunet_es_ubicacion_cuarentena(picking.location_dest_id):
                continue      # se mueve dentro de la propia cuarentena
            for linea in picking.move_line_ids:
                lote = linea.lot_id
                if not lote or not lote.amunet_cuarentena_fin:
                    continue
                if lote.amunet_cuarentena_estado == 'en_curso':
                    raise UserError(_(
                        'El lote %(lote)s todavía está en cuarentena.\n\n'
                        'Entró el %(ini)s y cumple el %(fin)s. Hasta entonces '
                        'no se le genera el análisis, así que no puede salir '
                        'de Control de calidad.',
                        lote=lote.name or '',
                        ini=lote.amunet_cuarentena_inicio.strftime('%d/%m/%Y'),
                        fin=lote.amunet_cuarentena_fin.strftime('%d/%m/%Y'),
                    ))
                analisis = self.env['amunet.quality.check'].sudo().search(
                    [('lot_id', '=', lote.id)])
                if not analisis:
                    raise UserError(_(
                        'El lote %(lote)s cumplió su cuarentena pero todavía '
                        'no tiene análisis.\n\n'
                        'Se genera solo, una vez al día. Si corre prisa, '
                        'pídele a Calidad que lo genere desde el lote.',
                        lote=lote.name or '',
                    ))
                # Aprobado = terminado Y con dictamen favorable. Es el mismo
                # par que ya usa el expediente del lote
                # (amunet_lot_dossier: state != 'done' or global_result != 'pass'),
                # para que no haya dos definiciones de "aprobado" en la casa.
                # OJO: el analisis NO tiene un estado 'approved'; sus estados son
                # draft / in_progress / pending / awaiting_reception / done, y el
                # dictamen vive aparte en global_result.
                if not any(a.state == 'done' and a.global_result == 'pass'
                           for a in analisis):
                    raise UserError(_(
                        'El análisis del lote %(lote)s todavía no está '
                        'aprobado.\n\n'
                        'Estado: %(estados)s. Dictamen: %(dictamen)s.\n\n'
                        'Calidad tiene que terminarlo y que salga aprobado '
                        'antes de que el material pase a Existencias.',
                        lote=lote.name or '',
                        estados=', '.join(sorted(set(analisis.mapped('state')))),
                        dictamen=', '.join(sorted(set(
                            analisis.mapped('global_result')))) or 'sin dictamen',
                    ))

        res = super().button_validate()

        # --- ENTRADA: arranca el reloj --------------------------------------
        # Despues del super() a proposito: hasta que la validacion no paso, el
        # material no esta en cuarentena y sellar la fecha seria mentir.
        for picking in self:
            if not picking._amunet_es_ubicacion_cuarentena(picking.location_dest_id):
                continue
            lotes = picking.move_line_ids.mapped('lot_id')
            if lotes:
                lotes._amunet_iniciar_cuarentena(picking=picking)
        return res
