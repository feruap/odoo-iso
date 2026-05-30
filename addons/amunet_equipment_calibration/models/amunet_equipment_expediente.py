# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AmunetEquipmentExpediente(models.Model):
    _name = 'amunet.equipment.expediente'
    _description = 'Expediente de Calificación de Equipo (ISO 13485 §7.5.6)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(
        string='Expediente',
        compute='_compute_name',
        store=True,
    )
    equipment_id = fields.Many2one(
        'amunet.equipment',
        string='Equipo',
        required=True,
        ondelete='restrict',
        tracking=True,
    )
    state = fields.Selection([
        ('en_proceso', 'En proceso'),
        ('vigente', 'Vigente'),
        ('obsoleto', 'Obsoleto'),
    ], string='Estado', default='en_proceso', required=True, tracking=True)
    equipment_serial = fields.Char(
        string='Código/ID',
        related='equipment_id.serial_number',
        store=False,
    )
    physical_location = fields.Char(string='Ubicación del documento')
    qualification_ids = fields.One2many(
        'amunet.equipment.calificacion',
        'expediente_id',
        string='Calificaciones',
    )
    notes = fields.Text(string='Notas')

    @api.depends('equipment_id.serial_number')
    def _compute_name(self):
        for rec in self:
            serial = rec.equipment_id.serial_number or ''
            if serial and serial.count('/') >= 2:
                parts = serial.split('/')
                family = parts[1]
                number = parts[2]
                rec.name = f'EXP-CAL/{family}/{number}'
            else:
                rec.name = serial or 'EXP-CAL/--/--'


class AmunetEquipmentCalificacion(models.Model):
    _name = 'amunet.equipment.calificacion'
    _description = 'Calificación de Equipo (CD/CI/CO/CE)'
    _rec_name = 'protocol_code'

    expediente_id = fields.Many2one(
        'amunet.equipment.expediente',
        string='Expediente',
        required=True,
        ondelete='cascade',
    )
    equipment_id = fields.Many2one(
        'amunet.equipment',
        string='Equipo',
        related='expediente_id.equipment_id',
        store=True,
    )
    qual_type = fields.Selection([
        ('cd', 'CD - Calificación de Diseño'),
        ('ci', 'CI - Calificación de Instalación'),
        ('co', 'CO - Calificación de Operación'),
        ('ce', 'CE - Calificación de Desempeño'),
    ], string='Tipo', required=True)
    protocol_code = fields.Char(
        string='Código Protocolo',
        compute='_compute_codes',
        store=True,
    )
    report_code = fields.Char(
        string='Código Reporte',
        compute='_compute_codes',
        store=True,
    )
    protocol_date = fields.Char(string='Fecha Protocolo', default='AGO/2024')
    report_date = fields.Char(string='Fecha Reporte', default='SEP/2024')
    responsible_id = fields.Many2one('res.users', string='Responsable')
    result = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ], string='Resultado', default='pendiente', required=True)
    physical_location = fields.Char(string='Ubicación del documento')
    notes = fields.Text(string='Notas')
    attachment_ids = fields.Many2many('ir.attachment', string='Adjuntos')

    @api.depends('qual_type', 'expediente_id.equipment_id.serial_number')
    def _compute_codes(self):
        for rec in self:
            serial = rec.expediente_id.equipment_id.serial_number or ''
            if rec.qual_type and serial and serial.count('/') >= 2:
                parts = serial.split('/')
                family = parts[1]
                number = parts[2]
                qual = rec.qual_type.upper()
                rec.protocol_code = f'P{qual}{family}-{number}'
                rec.report_code = f'R{qual}{family}-{number}'
            else:
                rec.protocol_code = False
                rec.report_code = False
