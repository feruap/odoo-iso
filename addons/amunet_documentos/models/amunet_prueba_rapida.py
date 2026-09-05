# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api


class AmunetPruebaRapida(models.Model):
    _name = 'amunet.prueba.rapida'
    _description = 'Datos de pruebas rápidas'
    _rec_name = 'nombre'
    _order = 'nombre_texto'

    nombre      = fields.Html(string='Nombre de la prueba (Denominación distintiva)', required=True, sanitize_tags=False)
    nombre_texto = fields.Char(
        string='Nombre (texto plano)',
        compute='_compute_nombre_texto',
        store=True,
    )
    muestra     = fields.Char(string='Muestra')
    descripcion = fields.Html(string='Descripción (Denominación genérica)', sanitize_tags=False)

    @api.depends('nombre')
    def _compute_nombre_texto(self):
        for rec in self:
            rec.nombre_texto = re.sub(r'<[^>]+>', '', rec.nombre or '').strip()

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = re.sub(r'<[^>]+>', '', rec.nombre or '').strip() or str(rec.id)
    codigo      = fields.Char(string='Código')
    referencia  = fields.Char(string='Referencia')
    caducidad_autorizada  = fields.Char(string='Caducidad de la prueba')
    registro_sanitario    = fields.Char(string='Registro sanitario', default='No aplica')
    fecha_emision_rs      = fields.Date(string='Fecha de emisión RS')
    fecha_vencimiento_rs  = fields.Date(string='Fecha de vencimiento RS')
