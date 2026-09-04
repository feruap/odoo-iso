# -*- coding: utf-8 -*-
"""Traspaso de producto terminado de la Fabrica a Distribucion.

Es la entrada principal de ADT: la fabrica entrega lo que ya esta listo para
venderse y Distribucion lo recibe. Se hace con un documento propio -no moviendo
existencias a mano- para que quede el rastro de que salio de fabrica y que entro
a la venta, con quien y cuando.

El otro camino de entrada es la compra propia de Distribucion, que llega
directo a ADT sin pasar por fabrica y no necesita nada especial: basta con que
la orden de compra apunte al almacen ADT.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError

CODIGO_ADT = 'ADT'
CODIGO_APT = 'APT'


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    @api.model
    def _amunet_almacen(self, codigo):
        alm = self.sudo().search([('code', '=', codigo)], limit=1)
        if not alm:
            raise UserError(_(
                'No existe el almacen %s. Si en esta instalacion se llama de '
                'otra forma, hay que ajustarlo antes de traspasar.') % codigo)
        return alm


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    amunet_es_traspaso_distribucion = fields.Boolean(
        string='Traspaso a Distribucion', copy=False, readonly=True,
        help='Marca el documento con el que la fabrica entrega producto '
             'terminado al almacen de Distribucion.')


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def action_amunet_traspasar_a_distribucion(self):
        """Prepara el traspaso de lo seleccionado, de APT a ADT.

        Se abre el documento SIN validar a proposito: quien entrega revisa las
        cantidades y lo confirma. Igual que cualquier traslado, no un
        movimiento silencioso.
        """
        Warehouse = self.env['stock.warehouse']
        origen = Warehouse._amunet_almacen(CODIGO_APT)
        destino = Warehouse._amunet_almacen(CODIGO_ADT)

        quants = self.filtered(lambda q: q.quantity > 0)
        if not quants:
            raise UserError(_('Selecciona existencia con cantidad mayor a 0.'))

        fuera = quants.filtered(
            lambda q: q.location_id.warehouse_id != origen)
        if fuera:
            raise UserError(_(
                'Solo se traspasa desde %(alm)s. Estas fuera de ese almacen:\n%(l)s'
            ) % {'alm': origen.name,
                 'l': '\n'.join('  - %s en %s' % (q.product_id.display_name,
                                                  q.location_id.complete_name)
                                for q in fuera[:10])})

        tipo = self.env['stock.picking.type'].sudo().search([
            ('code', '=', 'internal'),
            ('warehouse_id', '=', destino.id),
        ], limit=1)
        if not tipo:
            raise UserError(_(
                'El almacen %s no tiene un tipo de operacion interna.') % destino.name)

        picking = self.env['stock.picking'].sudo().create({
            'picking_type_id': tipo.id,
            'location_id': origen.lot_stock_id.id,
            'location_dest_id': destino.lot_stock_id.id,
            'origin': _('Traspaso Fabrica -> Distribucion'),
            'amunet_es_traspaso_distribucion': True,
            'move_ids': [(0, 0, {
                'product_id': q.product_id.id,
                'product_uom_qty': q.quantity,
                'product_uom': q.product_id.uom_id.id,
                'location_id': q.location_id.id,
                'location_dest_id': destino.lot_stock_id.id,
            }) for q in quants],
        })
        picking.action_confirm()
        picking.action_assign()

        # Odoo FUSIONA los movimientos del mismo producto entre las mismas
        # ubicaciones. Si se dejara asi, dos lotes con caducidades distintas
        # quedarian como una sola linea con un solo lote: se perderia la
        # trazabilidad justo en el paso que la necesita, porque de aqui el
        # producto sale al cliente.
        # Por eso las lineas de operacion se rehacen a mano, UNA POR LOTE.
        MoveLine = self.env['stock.move.line'].sudo()
        for move in picking.move_ids:
            suyos = quants.filtered(lambda q: q.product_id == move.product_id)
            if not suyos:
                continue
            move.move_line_ids.unlink()
            for q in suyos:
                MoveLine.create({
                    'move_id': move.id,
                    'picking_id': picking.id,
                    'product_id': q.product_id.id,
                    'product_uom_id': q.product_id.uom_id.id,
                    'lot_id': q.lot_id.id or False,
                    'quantity': q.quantity,
                    'location_id': q.location_id.id,
                    'location_dest_id': destino.lot_stock_id.id,
                })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Traspaso a Distribucion'),
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'view_mode': 'form',
            'target': 'current',
        }
