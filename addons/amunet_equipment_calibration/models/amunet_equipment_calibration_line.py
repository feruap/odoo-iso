# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AmunetEquipmentCalibration(models.Model):
    _name = 'amunet.equipment.calibration'
    _description = 'Certificado de Calibración de Equipo'
    _order = 'calibration_date desc, id desc'

    equipment_id = fields.Many2one('amunet.equipment', string='Equipo', required=True, ondelete='cascade')
    
    calibration_date = fields.Date(string='Fecha de Calibración', required=True, default=fields.Date.context_today)
    expiration_date = fields.Date(string='Fecha de Vencimiento', required=True)
    
    certificate_file = fields.Binary(string='Certificado PDF (Laboratorio)', attachment=True)
    certificate_filename = fields.Char(string='Nombre Archivo')
    
    lab_name = fields.Char(string='Laboratorio Emisor / Proveedor')
    notes = fields.Text(string='Observaciones')

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Aprobado'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='draft', required=True)

    @api.constrains('calibration_date', 'expiration_date')
    def _check_dates(self):
        for record in self:
            if record.expiration_date and record.calibration_date and record.expiration_date <= record.calibration_date:
                raise ValidationError("La Fecha de Vencimiento debe ser posterior a la Fecha de Calibración.")

    def action_approve(self):
        for record in self:
            record.state = 'done'
            # Al aprobar un certificado vigente, reactivar el equipo si la vigencia es futura
            if record.expiration_date and record.expiration_date >= fields.Date.today():
                if record.equipment_id.state == 'out_of_service':
                    record.equipment_id.state = 'active'
                    record.equipment_id.message_post(body=f"✅ Equipo reactivado automáticamente al aprobar la calibración válida hasta {record.expiration_date}.")

    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'

    def action_draft(self):
        for record in self:
            record.state = 'draft'
