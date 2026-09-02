# -*- coding: utf-8 -*-
"""Ajuste de columnas del documento de Recepciones de PT.

El documento de ingreso a PT reusa el formulario de traslados, y con el se
arrastran columnas hechas para la recepcion de MATERIA PRIMA:

  - "Lote de proveedor": aqui no hay proveedor. El material lo fabricamos
    nosotros y su lote ya esta en la columna de al lado. Siempre vacia.
  - "Cant. solicitada": editable, pero la validacion la IGNORA (toma lo que
    firmo Produccion). Invitaba a corregir un numero que no hace nada; si el
    almacen cuenta distinto no corrige, RECHAZA, y el material regresa
    completo.

En vez de quitar la comparacion, se conserva como dato de solo lectura con el
nombre que le corresponde aqui: "Entregado por Produccion". Asi quien recibe ve
lado a lado lo que le entregaron y lo que tiene, que es lo que necesita para
decidir si valida o rechaza.

El filtro va por el tipo de operacion de PT, no por "traslado interno": esas
columnas SI son necesarias en las recepciones de Karla y en la conversion de
combos, y no se tocan.
"""

from odoo import api, fields, models

SEQ_INGRESO_PT = 'APTIN'


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    amunet_es_ingreso_pt = fields.Boolean(
        string='Es ingreso a PT',
        compute='_compute_amunet_es_ingreso_pt',
        help='Marca el documento con el que el almacen de Producto Terminado '
             'recibe lo que entrega Produccion. Solo sirve para acomodar las '
             'columnas de la pantalla.')

    @api.depends('picking_type_id')
    def _compute_amunet_es_ingreso_pt(self):
        for rec in self:
            rec.amunet_es_ingreso_pt = (
                rec.picking_type_id.sequence_code == SEQ_INGRESO_PT)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    amunet_pt_entregado = fields.Float(
        string='Entregado por Produccion',
        related='qty_demanded', readonly=True,
        digits='Product Unit',
        help='Lo que Produccion firmo con su PIN. Si no coincide con lo que '
             'cuentas, no lo corrijas: rechaza la entrega y el material '
             'regresa completo a Produccion.')
