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
    caducidad_autorizada = fields.Char(string='Caducidad autorizada')
