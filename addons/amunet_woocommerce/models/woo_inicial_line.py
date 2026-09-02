# -*- coding: utf-8 -*-
"""Renglones de inventario inicial que captura el almacen.

Cada renglon es UN lote fisico: numero de lote, caducidad y piezas. El
almacen agrega los que necesite en la ficha del producto (pantalla de
mapeos) y los carga todos con un boton. Nada de esto pasa por Calidad ni
por una orden de fabricacion: es material anterior al sistema y entra como
ajuste de inventario con usuario, fecha y motivo.
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AmunetWooInicialLine(models.Model):
    _name = 'amunet.woo.inicial.line'
    _description = 'Inventario inicial - renglon de lote capturado por el almacen'
    _order = 'state asc, id desc'

    mapping_id = fields.Many2one(
        'amunet.woo.product.mapping', string='Producto (mapeo)',
        required=True, ondelete='cascade', index=True)
    product_id = fields.Many2one(
        related='mapping_id.product_id', store=True, string='Producto Odoo')
    lot_name = fields.Char(
        string='Lote',
        help='Numero de lote tal como viene en la caja. Si el material no '
             'trae lote, dejalo vacio y el sistema pone uno de inventario '
             'inicial para poder rastrearlo.')
    expiration_date = fields.Date(
        string='Caducidad',
        help='Obligatoria en productos que venden por caducidad (la tienda '
             'clasifica normal / corta / cortesia con esta fecha).')
    qty = fields.Float(string='Piezas', required=True, digits='Product Unit of Measure')
    nota = fields.Char(string='Observacion')
    state = fields.Selection([
        ('pending', 'Por cargar'),
        ('done', 'Cargado'),
    ], string='Estado', default='pending', required=True, index=True)
    lot_id = fields.Many2one('stock.lot', string='Lote en Odoo', readonly=True)
    cargado_por = fields.Many2one('res.users', string='Cargado por', readonly=True)
    cargado_en = fields.Datetime(string='Cargado el', readonly=True)

    _CAMPOS_FIJOS = ('lot_name', 'expiration_date', 'qty', 'mapping_id')

    @api.constrains('qty')
    def _check_qty(self):
        for rec in self:
            if rec.qty <= 0:
                raise ValidationError(_(
                    'El renglon del lote %s tiene que traer piezas (mayor que cero).'
                ) % (rec.lot_name or _('sin nombre')))

    @api.constrains('expiration_date', 'mapping_id')
    def _check_caducidad(self):
        for rec in self:
            if rec.expiration_date:
                continue
            producto = rec.mapping_id.product_id
            backend = rec.mapping_id.backend_id
            maneja = True
            if producto and backend and hasattr(backend, '_maneja_caducidad'):
                maneja = backend.sudo()._maneja_caducidad(producto)
            if maneja:
                raise ValidationError(_(
                    '%s vende por caducidad: captura la fecha de caducidad del '
                    'lote %s. Sin ella la tienda no lo puede clasificar.'
                ) % (producto.display_name if producto else rec.mapping_id.woo_sku,
                     rec.lot_name or _('sin nombre')))

    def write(self, vals):
        cambia = set(vals) & set(self._CAMPOS_FIJOS)
        if cambia and any(r.state == 'done' for r in self):
            raise UserError(_(
                'Este renglon ya se cargo al anaquel; no se puede cambiar. '
                'Si el dato estaba mal, agrega otro renglon con la diferencia.'))
        return super().write(vals)

    def unlink(self):
        if any(r.state == 'done' for r in self):
            raise UserError(_(
                'Un renglon ya cargado no se borra: es el rastro del ajuste de '
                'inventario. Si sobra material, ajustalo en Inventario.'))
        return super().unlink()

    def action_cargar(self):
        """Carga solo estos renglones (desde la lista de renglones)."""
        mapeos = self.filtered(lambda l: l.state == 'pending').mapped('mapping_id')
        if not mapeos:
            raise UserError(_('No hay renglones por cargar.'))
        return mapeos.action_cargar_inventario_inicial()