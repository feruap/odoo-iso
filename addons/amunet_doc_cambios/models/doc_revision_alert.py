from odoo import models, fields


class DocRevisionAlert(models.Model):
    """Modelo legacy — sin uso activo."""
    _name = 'amunet.doc.revision.alert'
    _description = 'Alerta de revisión de manual (legacy)'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(readonly=True, copy=False, default='Nueva alerta')
    production_name = fields.Char(readonly=True, store=True)
    summary = fields.Html(readonly=True)
    state = fields.Selection([
        ('pending', 'Pendiente'),
        ('yes', 'Sí'),
        ('no', 'No'),
    ], default='pending', required=True)
