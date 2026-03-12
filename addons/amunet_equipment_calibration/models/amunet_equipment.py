# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date

class AmunetEquipment(models.Model):
    _name = 'amunet.equipment'
    _description = 'Equipo de Medición (ISO 13485 Cláusula 7.6)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre del Equipo', required=True, tracking=True)
    serial_number = fields.Char(string='Número de Serie / Fabricante', tracking=True)
    brand = fields.Char(string='Marca')
    model_name = fields.Char(string='Modelo')
    department = fields.Selection([
        ('ALMACÉN DE MATERIA PRIMA', 'Almacén de Materia Prima'),
        ('SOLUCIONES', 'Soluciones'),
        ('LECTURA Y SECADO', 'Lectura y Secado'),
        ('INYECCIÓN', 'Inyección'),
        ('LAMINADO, SECADO Y CORTE', 'Laminado, Secado y Corte'),
        ('ENCARTUCHADO', 'Encartuchado'),
        ('ACONDICIONADO 1', 'Acondicionado 1'),
        ('ACONDICIONADO 2', 'Acondicionado 2'),
        ('ALMACÉN TEMPORAL DE PRODUCTO TERMINADO', 'Almacén Temporal de Producto Terminado'),
        ('ESTABILIDAD', 'Estabilidad'),
        ('CONTROL DE CALIDAD', 'Control de Calidad'),
        ('DESARROLLO', 'Desarrollo'),
        ('ALMACÉN DE PRODUCTO TERMINADO', 'Almacén de Producto Terminado')
    ], string='Departamento', tracking=True)
    location_id = fields.Many2one('stock.location', string='Ubicación')
    
    state = fields.Selection([
        ('active', 'Activo'),
        ('maintenance', 'En Mantenimiento / Calibración'),
        ('out_of_service', 'Fuera de Servicio')
    ], string='Estado', default='active', tracking=True, required=True)

    calibration_line_ids = fields.One2many(
        'amunet.equipment.calibration', 
        'equipment_id', 
        string='Historial de Calibración'
    )

    next_calibration_date = fields.Date(
        string='Próxima Calibración', 
        compute='_compute_next_calibration', 
        store=True,
        tracking=True
    )

    @api.depends('calibration_line_ids.state', 'calibration_line_ids.expiration_date')
    def _compute_next_calibration(self):
        for equipment in self:
            # Buscar el certificado activo más reciente
            active_calibrations = equipment.calibration_line_ids.filtered(lambda c: c.state == 'done')
            if active_calibrations:
                # Tomar la fecha de expiración más lejana (o la de creación más reciente)
                latest_calibration = active_calibrations.sorted(key=lambda c: c.expiration_date, reverse=True)[0]
                equipment.next_calibration_date = latest_calibration.expiration_date
            else:
                equipment.next_calibration_date = False

    @api.constrains('state', 'next_calibration_date')
    def _check_calibration_validity(self):
        """ Validación en tiempo real (si alguien intenta activar un equipo vencido) """
        for equipment in self:
            if equipment.state == 'active' and equipment.next_calibration_date:
                if equipment.next_calibration_date < date.today():
                    raise ValidationError(f"El equipo '{equipment.name}' no puede estar 'Activo' porque su calibración venció el {equipment.next_calibration_date}.")

    @api.model
    def _cron_check_calibration_status(self):
        """ 
        CRON Job diario para buscar equipos Vencidos y forzarlos a Fuera de Servicio
        (Regla Fuerte No. 1)
        """
        today = date.today()
        expired_equipments = self.search([
            ('state', '=', 'active'),
            ('next_calibration_date', '!=', False),
            ('next_calibration_date', '<', today)
        ])
        
        for eq in expired_equipments:
            eq.write({
                'state': 'out_of_service'
            })
            # Dejar mensaje en el chatter para auditoría
            eq.message_post(body=f"🔴 El sistema ha cambiado automáticamente el estado a 'Fuera de Servicio'. Motivo: La calibración caducó el {eq.next_calibration_date}.")
