# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import AccessError


class AmunetBitacoraAuditLog(models.Model):
    _name = 'amunet.bitacora.audit.log'
    _description = 'Log de auditoría de bitácoras (append-only)'
    _order = 'create_date desc, id desc'

    entry_id = fields.Many2one(
        'amunet.bitacora.entry', string='Registro', required=True, index=True, ondelete='restrict')
    event = fields.Char(string='Evento', required=True)
    user_id = fields.Many2one('res.users', string='Usuario', required=True)
    detail = fields.Text(string='Detalle')

    def write(self, vals):
        raise AccessError(_('El log de auditoría es append-only y no se puede modificar.'))

    def unlink(self):
        if not self.env.su:
            raise AccessError(_('El log de auditoría no se puede eliminar.'))
        return super().unlink()
