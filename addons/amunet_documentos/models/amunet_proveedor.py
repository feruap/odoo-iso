# -*- coding: utf-8 -*-
from odoo import models, fields


class AmunetProveedor(models.Model):
    _name = 'amunet.proveedor'
    _description = 'Lista maestra de proveedores'
    _order = 'name'

    name = fields.Char(string='Proveedor', required=True)

    tipo_suministro = fields.Selection([
        ('bien', 'Bien'),
        ('servicio', 'Servicio'),
    ], string='Bien o Servicio')

    ubicacion = fields.Selection([
        ('nacional', 'Nacional'),
        ('internacional', 'Internacional'),
    ], string='Ubicación')

    suministra = fields.Text(string='Productos/Servicios suministrados')

    impacto = fields.Selection([
        ('alto', 'Alto'),
        ('medio', 'Medio'),
        ('bajo', 'Bajo'),
    ], string='Impacto')

    estatus = fields.Selection([
        ('calificado', 'Calificado'),
        ('na', 'No aplica'),
    ], string='Estatus', default='na')

    notas = fields.Text(string='Notas')
