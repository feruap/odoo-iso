# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessDenied

class AmunetQualityAuditLog(models.Model):
    """
    Log de Auditoría para cumplimiento ISO 13485:4.2.1.
    Registra cambios críticos en datos (Old Value -> New Value) con trazabilidad completa.
    """
    _name = 'amunet.quality.audit.log'
    _description = 'Audit Log - ISO 13485'
    _order = 'create_date desc'

    model_name = fields.Char(string='Modelo', required=True, index=True)
    res_id = fields.Integer(string='ID Recurso', required=True, index=True)
    res_name = fields.Char(string='Recurso (Nombre)')
    
    user_id = fields.Many2one('res.users', string='Usuario', required=True, default=lambda self: self.env.user)
    field_name = fields.Char(string='Campo Modificado', required=True)
    field_description = fields.Char(string='Descripción del Campo')
    
    old_value = fields.Text(string='Valor Anterior')
    new_value = fields.Text(string='Valor Nuevo')
    
    change_date = fields.Datetime(string='Fecha Cambio', default=fields.Datetime.now)
    # ip_address = fields.Char(string='IP Address') # Opcional si se puede obtener del request
    
    justification = fields.Char(string='Justificación') # Para cambios en registros finalizados

    def write(self, vals):
        """Audit logs must be immutable (21 CFR Part 11)."""
        if not self.env.context.get('install_mode') and not self.env.su:
            raise AccessDenied(_("Los registros de auditoría no pueden ser modificados para garantizar la integridad de los datos."))
        return super(AmunetQualityAuditLog, self).write(vals)

    def unlink(self):
        """Audit logs must be immutable (21 CFR Part 11)."""
        if not self.env.context.get('install_mode') and not self.env.su:
            raise AccessDenied(_("Los registros de auditoría no pueden ser eliminados para garantizar la integridad de los datos."))
        return super(AmunetQualityAuditLog, self).unlink()
