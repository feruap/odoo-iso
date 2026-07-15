# -*- coding: utf-8 -*-
from odoo import models, fields


class AmunetQualityCheckEquipmentUnit(models.Model):
    _name = 'amunet.quality.check.equipment.unit'
    _description = 'Registro Unitario de Equipo en Análisis de Calidad'
    _order = 'sequence, id'

    check_id = fields.Many2one(
        'amunet.quality.check', string='Análisis', required=True, ondelete='cascade')

    sequence = fields.Integer(string='#', default=10)

    serial_number = fields.Char(string='No. de serie')

    # Campos genéricos (Vórtex y otros)
    result_apariencia = fields.Char(string='Apariencia')
    result_funcionalidad = fields.Char(string='Funcionalidad')
    result_dimensiones = fields.Char(string='Dimensiones', help='Dejar vacío si no aplica')

    # Campos Termobloque (EQTER01, EQTER02)
    temp_pozo_a = fields.Float(string='Temp A (°C)', digits=(5, 1))
    temp_pozo_b = fields.Float(string='Temp B (°C)', digits=(5, 1))
    temp_pozo_c = fields.Float(string='Temp C (°C)', digits=(5, 1))
    temp_pozo_d = fields.Float(string='Temp D (°C)', digits=(5, 1))
    temp_pozo_e = fields.Float(string='Temp E (°C)', digits=(5, 1))
    temp_termometro = fields.Float(string='Temp Termómetro (°C)', digits=(5, 1))
    tiempo_alcanzar_temp = fields.Float(string='Tiempo (min)', digits=(5, 1))
    diam_grande = fields.Char(string='Diám. Grande')
    diam_chico = fields.Char(string='Diám. Chico')

    status = fields.Selection([
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
    ], string='Estatus', required=True, default='approved')

    observations = fields.Text(string='Observaciones')
