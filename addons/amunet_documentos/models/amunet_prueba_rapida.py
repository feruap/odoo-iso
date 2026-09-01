# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api


class AmunetPruebaRapida(models.Model):
    _name = 'amunet.prueba.rapida'
    _description = 'Datos de pruebas rápidas'
    _rec_name = 'nombre'
    _order = 'nombre'

    nombre      = fields.Html(string='Nombre de la prueba (Denominación distintiva)', required=True, sanitize_tags=False)
    muestra     = fields.Char(string='Muestra')
    descripcion = fields.Html(string='Descripción (Denominación genérica)', sanitize_tags=False)

    def _compute_display_name(self):
        for rec in self:
            texto = re.sub(r'<[^>]+>', '', rec.nombre or '')
            rec.display_name = texto.strip() or str(rec.id)
    codigo      = fields.Char(string='Código')
    referencia  = fields.Char(string='Referencia')
    caducidad_autorizada  = fields.Char(string='Caducidad de la prueba')
    registro_sanitario    = fields.Char(string='Registro sanitario')
    fecha_emision_rs      = fields.Date(string='Fecha de emisión RS')
    fecha_vencimiento_rs  = fields.Date(string='Fecha de vencimiento RS')
