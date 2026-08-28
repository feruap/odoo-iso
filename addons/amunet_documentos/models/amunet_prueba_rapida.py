# -*- coding: utf-8 -*-
from odoo import models, fields


class AmunetPruebaRapida(models.Model):
    _name = 'amunet.prueba.rapida'
    _description = 'Datos de pruebas rápidas'
    _order = 'nombre'

    nombre      = fields.Char(string='Nombre de la prueba (Denominación distintiva)', required=True)
    muestra     = fields.Char(string='Muestra')
    descripcion = fields.Text(string='Descripción (Denominación genérica)')
    codigo      = fields.Char(string='Código')
    referencia  = fields.Char(string='Referencia')
    caducidad_autorizada  = fields.Char(string='Caducidad de la prueba')
    registro_sanitario    = fields.Char(string='Registro sanitario')
    fecha_emision_rs      = fields.Date(string='Fecha de emisión RS')
    fecha_vencimiento_rs  = fields.Date(string='Fecha de vencimiento RS')
    es_lamp               = fields.Boolean(string='Es prueba LAMP/molecular', default=False)
