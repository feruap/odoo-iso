# -*- coding: utf-8 -*-
"""Pantalla para recibir una entrega de PT: cuantas piezas cuenta el almacen.

Por que existe: el conteo se capturaba en una columna del documento -"Cant.
real"- y quien recibe tenia que encontrarla. Si no la llenaba, el boton
rebotaba con un aviso y parecia que "no funcionaba" (paso con Luis el
2026-09-02, dos veces).

Ahora el boton pregunta. Una sola casilla, con lo que entrego Produccion al
lado para comparar. Si el numero no cuadra no deja pasar y ofrece rechazar,
que es la regla: una entrega no se acepta a medias.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AmunetRecibirPtWizard(models.TransientModel):
    _name = 'amunet.recibir.pt.wizard'
    _description = 'Recibir una entrega de producto terminado'

    entrega_id = fields.Many2one(
        'amunet.entrega.pt', string='Entrega', required=True, readonly=True)
    production_id = fields.Many2one(
        related='entrega_id.production_id', string='Orden', readonly=True)
    lot_id = fields.Many2one(
        related='entrega_id.lot_id', string='Lote', readonly=True)
    qty_entregada = fields.Float(
        related='entrega_id.quantity_delivered', string='Entregado por Produccion',
        readonly=True, digits='Product Unit')
    qty_contada = fields.Float(
        string='Piezas que estoy recibiendo', required=True,
        digits='Product Unit',
        help='Cuenta el material y escribe lo que de verdad tienes enfrente.')

    @api.model
    def abrir_para(self, entrega):
        if entrega.state != 'por_recibir':
            raise UserError(_(
                'La entrega %(n)s ya esta %(e)s: no hay nada que recibir.'
            ) % {'n': entrega.name, 'e': entrega.state})
        # Se prellena con lo que ya hubiera capturado en el documento, si lo
        # hizo; si no, en cero, para que tenga que contar.
        ya = 0.0
        if entrega.picking_ingreso_id:
            ya = sum(entrega.picking_ingreso_id.move_ids.move_line_ids.mapped(
                'quantity'))
        wiz = self.create([{'entrega_id': entrega.id, 'qty_contada': ya}])
        return {
            'type': 'ir.actions.act_window',
            'name': _('Recibir entrega de Produccion'),
            'res_model': self._name,
            'res_id': wiz.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_confirmar(self):
        self.ensure_one()
        entrega = self.entrega_id
        if self.qty_contada <= 0:
            raise UserError(_(
                'Escribe cuantas piezas estas recibiendo. Si no llego nada, '
                'usa RECHAZAR en vez de validar.'))
        if abs(self.qty_contada - entrega.quantity_delivered) > 0.0001:
            raise UserError(_(
                'Estas recibiendo %(contado)s pza(s) pero Produccion entrego '
                '%(entregado)s del lote %(lote)s.\n\n'
                'Una entrega no se acepta a medias. Cierra esta ventana y usa '
                'RECHAZAR: el material regresa completo a Produccion, ellos '
                'aclaran la diferencia y vuelven a entregar.'
            ) % {'contado': self.qty_contada,
                 'entregado': entrega.quantity_delivered,
                 'lote': entrega.lot_id.name or ''})
        # El conteo se escribe en el documento antes de validar: asi queda
        # registrado lo que conto el almacen, no lo que dijo Produccion.
        for linea in entrega.picking_ingreso_id.sudo().move_ids.move_line_ids:
            linea.quantity = self.qty_contada
        return entrega.action_entrega_pt_validar()
