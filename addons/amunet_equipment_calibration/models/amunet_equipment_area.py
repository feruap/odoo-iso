# -*- coding: utf-8 -*-

from odoo import models, fields


class AmunetEquipmentArea(models.Model):
    _name = 'amunet.equipment.area'
    _description = 'Área — Protocolo y Reporte de Área (ISO 13485)'
    _rec_name = 'name'
    _order = 'sequence, id'

    name = fields.Char(string='Área', required=True)
    doc_type = fields.Selection([
        ('fisica', 'Física'),
        ('digital', 'Digital'),
    ], string='Documentación', default='fisica', required=True)
    protocol_code = fields.Char(string='Código Protocolo', required=True)
    report_code = fields.Char(string='Código Reporte', required=True)
    state = fields.Selection([
        ('vigente', 'Vigente'),
        ('obsoleto', 'Obsoleto'),
    ], string='Estatus', default='vigente', required=True)
    parent_id = fields.Many2one(
        'amunet.equipment.area',
        string='Área Padre',
        ondelete='restrict',
    )
    child_ids = fields.One2many(
        'amunet.equipment.area',
        'parent_id',
        string='Subáreas',
    )
    protocol_date = fields.Char(string='Fecha Protocolo')
    report_date = fields.Char(string='Fecha Reporte')
    sequence = fields.Integer(string='Secuencia', default=10)
    notes = fields.Text(string='Notas')
