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

from odoo import _, api, fields, models
from odoo.exceptions import UserError

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


class StockPickingEntregaPt(models.Model):
    """Los botones de la entrega, tambien en el documento de Recepciones.

    Quien recibe llega al documento, no a la pantalla de la entrega. Aqui se le
    dan los mismos botones para que pueda cerrar donde ya esta.
    """
    _inherit = 'stock.picking'

    amunet_entrega_pt_id = fields.Many2one(
        'amunet.entrega.pt', string='Entrega de PT',
        compute='_compute_amunet_entrega_pt_id',
        help='La entrega que genero este documento, si la hubo.')
    amunet_entrega_pt_state = fields.Selection(
        related='amunet_entrega_pt_id.state', string='Estado de la entrega')

    @api.depends('picking_type_id')
    def _compute_amunet_entrega_pt_id(self):
        Entrega = self.env['amunet.entrega.pt'].sudo()
        for rec in self:
            rec.amunet_entrega_pt_id = Entrega.search(
                [('picking_ingreso_id', '=', rec.id)], limit=1)

    def _amunet_entrega_pt_o_error(self):
        self.ensure_one()
        if not self.amunet_entrega_pt_id:
            raise UserError(_(
                'Este documento no viene de una entrega de Produccion.'))
        return self.amunet_entrega_pt_id

    def action_entrega_pt_validar_desde_picking(self):
        return self._amunet_entrega_pt_o_error().action_entrega_pt_validar()

    def action_entrega_pt_rechazar_desde_picking(self):
        return self._amunet_entrega_pt_o_error().action_entrega_pt_rechazar()

    def action_entrega_pt_abrir(self):
        entrega = self._amunet_entrega_pt_o_error()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Entrega de PT'),
            'res_model': 'amunet.entrega.pt',
            'res_id': entrega.id,
            'view_mode': 'form',
            'target': 'current',
        }
