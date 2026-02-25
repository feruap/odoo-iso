# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AmunetQualityTecnoIncident(models.Model):
    _name = 'amunet.quality.tecno.incident'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'amunet.tecno.mixin']
    _description = 'Reporte de Incidente de Tecnovigilancia (NOM-240)'
    _order = 'notification_date desc, id desc'

    name = fields.Char(
        string='Folio de Incidente',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nuevo')
    )
    
    description = fields.Text(string='Descripción del Evento')
    resolved = fields.Boolean(string='Cerrado / Resuelto', default=False)
    
    notification_date = fields.Datetime(related='tecno_notification_date', readonly=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nuevo')) == _('Nuevo'):
                vals['name'] = self.env['ir.sequence'].next_by_code('amunet.quality.tecno.incident') or _('Nuevo')
        return super(AmunetQualityTecnoIncident, self).create(vals_list)
