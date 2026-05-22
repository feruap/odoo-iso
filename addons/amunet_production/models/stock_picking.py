# -*- coding: utf-8 -*-
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

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
        return res

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
