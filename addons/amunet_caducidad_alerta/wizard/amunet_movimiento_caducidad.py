# -*- coding: utf-8 -*-
"""Confirmar el movimiento fisico de un lote al anaquel que le toca.

El semaforo dice que un lote ya cambio de condicion (por ejemplo, paso de
normal a caducidad corta) pero la mercancia sigue en el anaquel anterior. Este
asistente es el paso que cierra el circulo: la persona del almacen mueve las
cajas, entra aqui, revisa cuantas piezas movio y confirma. Odoo genera un
traslado interno real -con folio, fecha y usuario- y el lote deja de aparecer
en la lista de pendientes.

No se mueve inventario por detras: siempre queda un stock.picking validado que
se puede auditar, que es lo que pide ISO 13485.
"""
from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError


class AmunetMovimientoCaducidad(models.TransientModel):
    _name = 'amunet.movimiento.caducidad'
    _description = 'Confirmar movimiento de lotes por caducidad'

    lot_ids = fields.Many2many('stock.lot', string='Lotes')
    linea_ids = fields.One2many(
        'amunet.movimiento.caducidad.linea', 'wizard_id', string='Que se mueve')
    nota = fields.Char(
        string='Nota para el traslado',
        help='Queda en el documento del traslado. Por ejemplo, quien reviso el anaquel.')
    sin_pendientes = fields.Boolean(
        string='Sin nada que mover', compute='_compute_sin_pendientes')

    @api.depends('linea_ids')
    def _compute_sin_pendientes(self):
        for wiz in self:
            wiz.sin_pendientes = not wiz.linea_ids

    # ------------------------------------------------------------------
    @api.model
    def default_get(self, campos):
        valores = super().default_get(campos)
        lotes = self.env['stock.lot'].browse(self.env.context.get('active_ids', []))
        lotes = lotes.filtered(lambda l: l._name == 'stock.lot')
        valores['lot_ids'] = [Command.set(lotes.ids)]
        lineas = []
        for lote in lotes:
            destino = lote._amunet_destino_esperado()
            if not destino:
                continue
            for quant in lote._amunet_quants_movibles(destino):
                lineas.append(Command.create({
                    'lot_id': lote.id,
                    'product_id': quant.product_id.id,
                    'location_origen_id': quant.location_id.id,
                    'location_destino_id': destino.id,
                    'cantidad_en_anaquel': quant.quantity,
                    'cantidad_reservada': quant.reserved_quantity,
                    'cantidad': max(quant.quantity - quant.reserved_quantity, 0.0),
                }))
        valores['linea_ids'] = lineas
        return valores

    # ------------------------------------------------------------------
    def action_confirmar(self):
        self.ensure_one()
        lineas = self.linea_ids.filtered(lambda l: l.cantidad > 0)
        if not lineas:
            raise UserError(_(
                'No hay nada que mover. Captura al menos una cantidad mayor que cero.'))

        pares = {}
        for linea in lineas:
            pares.setdefault(
                (linea.location_origen_id, linea.location_destino_id), []).append(linea)

        Picking = self.env['stock.picking']
        pickings = Picking.browse()
        for (origen, destino), grupo in pares.items():
            tipo = self._amunet_tipo_traslado(origen, destino)
            picking = Picking.create({
                'picking_type_id': tipo.id,
                'location_id': origen.id,
                'location_dest_id': destino.id,
                'origin': self.nota or _('Semaforo de caducidad'),
            })
            # Un movimiento por linea, creado uno a uno para no perder de vista
            # cual lote va en cual: dos lineas pueden ser el mismo producto en
            # lotes distintos.
            parejas = []
            for linea in grupo:
                movimiento = self.env['stock.move'].create({
                    'picking_id': picking.id,
                    'product_id': linea.product_id.id,
                    'product_uom_qty': linea.cantidad,
                    'product_uom': linea.product_id.uom_id.id,
                    'location_id': origen.id,
                    'location_dest_id': destino.id,
                })
                parejas.append((movimiento, linea))
            picking.action_confirm()
            for movimiento, linea in parejas:
                movimiento.move_line_ids = [Command.clear(), Command.create({
                    'product_id': linea.product_id.id,
                    'product_uom_id': linea.product_id.uom_id.id,
                    'lot_id': linea.lot_id.id,
                    'quantity': linea.cantidad,
                    'location_id': origen.id,
                    'location_dest_id': destino.id,
                    'picking_id': picking.id,
                    'picked': True,
                })]
                movimiento.picked = True
            picking.button_validate()
            pickings |= picking

        ahora = fields.Datetime.now()
        lotes = lineas.mapped('lot_id')
        for lote in lotes:
            suyos = pickings.filtered(
                lambda p, l=lote: l in p.move_line_ids.mapped('lot_id'))
            lote.sudo().write({
                'amunet_movimiento_fecha': ahora,
                'amunet_movimiento_usuario_id': self.env.user.id,
                'amunet_movimiento_picking_id': suyos[:1].id or False,
            })
        lotes._amunet_recalcular_caducidad()

        if len(pickings) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'res_id': pickings.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return {
            'type': 'ir.actions.act_window',
            'name': _('Traslados generados'),
            'res_model': 'stock.picking',
            'domain': [('id', 'in', pickings.ids)],
            'view_mode': 'list,form',
            'target': 'current',
        }

    # ------------------------------------------------------------------
    def _amunet_tipo_traslado(self, origen, destino):
        """El tipo de operacion interna del almacen donde vive el anaquel."""
        Tipo = self.env['stock.picking.type']
        almacen = origen.warehouse_id or destino.warehouse_id
        if almacen and almacen.int_type_id:
            return almacen.int_type_id
        tipo = Tipo.search([
            ('code', '=', 'internal'),
            ('company_id', 'in', (self.env.company.id, False)),
        ], limit=1)
        if not tipo:
            raise UserError(_(
                'No hay un tipo de operacion de traslado interno configurado. '
                'Pide a sistemas que lo cree antes de confirmar movimientos.'))
        return tipo


class AmunetMovimientoCaducidadLinea(models.TransientModel):
    _name = 'amunet.movimiento.caducidad.linea'
    _description = 'Linea del movimiento de lotes por caducidad'

    wizard_id = fields.Many2one(
        'amunet.movimiento.caducidad', required=True, ondelete='cascade')
    lot_id = fields.Many2one('stock.lot', string='Lote', required=True, readonly=True)
    product_id = fields.Many2one(
        'product.product', string='Producto', required=True, readonly=True)
    condicion = fields.Selection(
        related='lot_id.amunet_condicion_caducidad', string='Condicion', readonly=True)
    caducidad = fields.Datetime(
        related='lot_id.expiration_date', string='Caduca', readonly=True)
    location_origen_id = fields.Many2one(
        'stock.location', string='Anaquel actual', required=True, readonly=True)
    location_destino_id = fields.Many2one(
        'stock.location', string='Anaquel destino', required=True)
    cantidad_en_anaquel = fields.Float(
        string='Hay en el anaquel', readonly=True, digits='Product Unit of Measure')
    cantidad_reservada = fields.Float(
        string='Comprometido en pedidos', readonly=True,
        digits='Product Unit of Measure',
        help='Piezas ya apartadas para pedidos. Muevelas solo si tambien cambias el pedido.')
    cantidad = fields.Float(
        string='Se movio', digits='Product Unit of Measure',
        help='Cuantas piezas moviste de verdad. Si moviste todo, deja el total.')

    @api.constrains('cantidad', 'cantidad_en_anaquel')
    def _check_cantidad(self):
        for linea in self:
            if linea.cantidad < 0:
                raise UserError(_('La cantidad movida no puede ser negativa.'))
            if linea.cantidad > linea.cantidad_en_anaquel:
                raise UserError(_(
                    'En %(anaquel)s solo hay %(hay)s de %(producto)s lote %(lote)s; '
                    'no puedes mover %(pide)s.',
                    anaquel=linea.location_origen_id.display_name,
                    hay=linea.cantidad_en_anaquel,
                    producto=linea.product_id.display_name,
                    lote=linea.lot_id.name,
                    pide=linea.cantidad))
