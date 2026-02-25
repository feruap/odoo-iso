# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import timedelta

class AmunetTecnoMixin(models.AbstractModel):
    _name = 'amunet.tecno.mixin'
    _description = 'Mixin para cumplimiento NOM-240 (Tecnovigilancia)'

    is_tecnovigilancia = fields.Boolean(
        string='Es Tecnovigilancia',
        default=False,
        help='Marque si este registro corresponde a un reporte de Tecnovigilancia (NOM-240).'
    )

    tecno_incident_type = fields.Selection([
        ('initial', 'Notificación Inicial'),
        ('followup', 'Reporte de Seguimiento'),
        ('final', 'Reporte Final'),
    ], string='Tipo de Incidente', help='Clasificación del reporte según NOM-240.')

    tecno_severity = fields.Selection([
        ('critical', 'IAG: Incidente Adverso Grave (Serio)'),
        ('major', 'IANG: Incidente Adverso No Grave (No Serio)'),
        ('minor', 'Otros Incidentes (No Serio)'),
    ], string='Severidad / Gravedad', help='Gravedad del incidente para determinar plazos de reporte.')

    tecno_patient_initials = fields.Char(string='Iniciales del Paciente')
    tecno_age = fields.Integer(string='Edad')
    tecno_gender = fields.Selection([
        ('m', 'Masculino'),
        ('f', 'Femenino'),
        ('o', 'Otro'),
    ], string='Género')

    tecno_product_lot = fields.Char(string='Lote del Producto', help='Lote involucrado en el incidente.')
    tecno_product_expiry = fields.Date(string='Fecha de Caducidad', help='Fecha de caducidad del dispositivo involucrado.')
    
    tecno_detection_date = fields.Datetime(
        string='Fecha de Detección',
        help='Fecha en que el usuario detectó el incidente.'
    )

    tecno_notification_date = fields.Datetime(
        string='Fecha de Reporte (Notificación)',
        default=fields.Datetime.now,
        help='Fecha en la que la empresa recibió la notificación del incidente.'
    )

    tecno_report_deadline = fields.Datetime(
        string='Fecha Límite de Reporte',
        compute='_compute_tecno_report_deadline',
        store=True,
        help='Fecha límite legal para presentar el reporte a COFEPRIS.'
    )

    @api.depends('tecno_notification_date', 'tecno_severity', 'is_tecnovigilancia')
    def _compute_tecno_report_deadline(self):
        """Cálculo de plazos legales según NOM-240-SSA1-2012."""
        for record in self:
            if record.is_tecnovigilancia and record.tecno_notification_date:
                days = 30 # Default: No graves
                if record.tecno_severity == 'critical':
                    days = 2 # 48 horas para casos críticos (IAG)
                elif record.tecno_severity == 'major':
                    days = 10 # IANG
                record.tecno_report_deadline = record.tecno_notification_date + timedelta(days=days)
            else:
                record.tecno_report_deadline = False
