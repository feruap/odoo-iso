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

    def action_print_lista_con_rs(self):
        docs = self.search(
            [('registro_sanitario', 'not in', [False, 'No aplica'])],
            order='nombre',
        )
        return self.env.ref(
            'amunet_documentos.action_report_prueba_rapida_con_rs'
        ).report_action(docs)

    def action_print_lista_sin_rs(self):
        docs = self.search(
            [('registro_sanitario', 'in', [False, 'No aplica'])],
            order='nombre',
        )
        return self.env.ref(
            'amunet_documentos.action_report_prueba_rapida_sin_rs'
        ).report_action(docs)
