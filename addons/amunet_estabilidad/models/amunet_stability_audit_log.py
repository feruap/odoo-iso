# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import AccessError


class AmunetStabilityAuditLog(models.Model):
    _name = 'amunet.stability.audit.log'
    _description = 'Log de auditoría de estabilidad (append-only)'
    _order = 'create_date desc, id desc'

    study_id = fields.Many2one(
        'amunet.stability.study', string='Estudio', required=True, index=True, ondelete='restrict')
    event = fields.Char(string='Evento', required=True)
    user_id = fields.Many2one('res.users', string='Usuario', required=True)
    detail = fields.Text(string='Detalle')

    def write(self, vals):
        raise AccessError(_('El log de auditoría es append-only y no se puede modificar.'))

    def unlink(self):
        if not self.env.su:
            raise AccessError(_('El log de auditoría no se puede eliminar.'))
        return super().unlink()
