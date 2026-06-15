from odoo import models, fields, api
from datetime import date, timedelta


class StockLotAlert(models.Model):
    _inherit = 'stock.lot'

    amunet_alert_level = fields.Selection([
        ('ok',      'Vigente'),
        ('soon',    'Por vencer'),
        ('expired', 'Vencido'),
    ], compute='_compute_amunet_alert_level', store=False)

    @api.depends('expiration_date')
    def _compute_amunet_alert_level(self):
        today = date.today()
        soon = today + timedelta(days=30)
        for lot in self:
            if not lot.expiration_date:
                lot.amunet_alert_level = 'ok'
            elif lot.expiration_date.date() <= today:
                lot.amunet_alert_level = 'expired'
            elif lot.expiration_date.date() <= soon:
                lot.amunet_alert_level = 'soon'
            else:
                lot.amunet_alert_level = 'ok'
