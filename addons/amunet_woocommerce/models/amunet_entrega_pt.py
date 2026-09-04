# -*- coding: utf-8 -*-
"""Entrega de producto terminado de Produccion al almacen de PT.

Modelo PROPIO, sin heredar de nada. Antes esto colgaba de
``amunet.woo.delivery`` (el rescate de entrega/recepcion de material para
venta), pero ese modelo no existe en produccion y su promocion es una decision
aparte que no se ha tomado. Se independizo para que la Entrega de PT pueda
llegar a produccion sin arrastrar trabajo sin aprobar (decision de Mery,
2026-09-02).

Solo se necesitaban cinco datos de aquel modelo -orden, producto, lote, piezas
y estado-, asi que la separacion sale barata.

Lo que ESTE modelo guarda es el acta de la entrega: quien entrego, cuanto, de
que lote y quien lo recibio. El movimiento de inventario vive en
``woo_entrega_pt.py``.
"""

from odoo import _, api, fields, models


class AmunetEntregaPt(models.Model):
    _name = 'amunet.entrega.pt'
    _description = 'Entrega de producto terminado al almacen de PT'
    _inherit = ['mail.thread']
    _order = 'delivered_date desc, id desc'

    name = fields.Char(
        string='Folio', readonly=True, copy=False, default='/')

    production_id = fields.Many2one(
        'mrp.production', string='Orden de fabricacion', required=True,
        ondelete='restrict', index=True, tracking=True,
        help='La entrega siempre sale de una orden: de ahi se resuelven el '
             'producto, el lote y la caducidad, sin recapturar.')
    company_id = fields.Many2one(
        'res.company', string='Compania', required=True,
        default=lambda self: self.env.company, index=True)
    product_id = fields.Many2one(
        'product.product', string='Producto', ondelete='restrict', index=True,
        tracking=True)
    lot_id = fields.Many2one(
        'stock.lot', string='Lote', ondelete='restrict', index=True,
        tracking=True)

    quantity_delivered = fields.Float(
        string='Piezas entregadas', required=True, tracking=True,
        digits='Product Unit',
        help='Lo que Produccion declara que esta entregando, firmado con PIN.')
    delivered_by = fields.Many2one(
        'res.users', string='Entregado por', readonly=True, index=True,
        default=lambda self: self.env.user, tracking=True)
    delivered_date = fields.Datetime(
        string='Fecha de entrega', readonly=True, required=True,
        default=fields.Datetime.now, tracking=True)

    state = fields.Selection([
        ('por_recibir', 'Por recibir'),
        ('recibida', 'Recibida'),
        ('rechazada', 'Rechazada'),
        ('cancelada', 'Cancelada'),
    ], string='Estado', default='por_recibir', required=True, tracking=True)

    notes = fields.Text(string='Notas de la entrega')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == '/':
                vals['name'] = self.env['ir.sequence'].sudo().next_by_code(
                    'amunet.entrega.pt') or '/'
            # El lote y el producto salen de la orden: no se recapturan.
            if vals.get('production_id') and not vals.get('lot_id'):
                prod = self.env['mrp.production'].browse(vals['production_id'])
                vals.setdefault('product_id', prod.product_id.id)
                lot = self._resolve_lot_from_production(prod)
                if lot:
                    vals['lot_id'] = lot.id
        return super().create(vals_list)

    @api.model
    def _resolve_lot_from_production(self, production):
        """Lote que produce una orden de fabricacion.

        Odoo 19 no tiene ``lot_producing_id``. Se resuelve, en orden:
        1) ``lot_producing_ids`` de la orden,
        2) el lote de los movimientos de producto terminado,
        3) por convencion de Amunet, el lote cuyo NOMBRE es el mismo que el de
           la orden (la orden ES el lote).
        """
        if not production:
            return self.env['stock.lot']
        lots = production.sudo().mapped('lot_producing_ids')
        lots = lots.filtered(lambda l: l.product_id == production.product_id)
        if lots:
            return lots[0]
        moves = production.sudo().move_finished_ids.filtered(
            lambda m: m.product_id == production.product_id)
        lots = moves.mapped('move_line_ids.lot_id')
        if lots:
            return lots[0]
        return self.env['stock.lot'].sudo().search([
            ('name', '=', production.name),
            ('product_id', '=', production.product_id.id),
        ], limit=1)
