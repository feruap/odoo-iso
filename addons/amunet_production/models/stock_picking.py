# -*- coding: utf-8 -*-
import logging

from odoo import fields, models

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
