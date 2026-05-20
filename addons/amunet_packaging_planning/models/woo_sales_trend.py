# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AmunetWooSalesTrend(models.Model):
    _name = 'amunet.woo.sales.trend'
    _description = 'Venta historica WooCommerce para tendencia de empaque'
    _order = 'sale_date desc, id desc'

    sale_date = fields.Date(string='Fecha venta', required=True, index=True)
    source = fields.Selection([
        ('woocommerce', 'WooCommerce'),
        ('manual_import', 'Importacion manual'),
        ('demo', 'Demo'),
    ], default='woocommerce', required=True)

    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Producto maestro',
        required=True,
        index=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Producto Odoo',
        domain="[('product_tmpl_id', '=', product_tmpl_id)]",
    )
    presentation_id = fields.Many2one(
        'amunet.packaging.presentation',
        string='Presentacion',
        required=True,
        domain="[('product_tmpl_id', '=', product_tmpl_id)]",
        index=True,
    )
    woo_order_id = fields.Char(string='Pedido Woo')
    woo_product_id = fields.Char(string='Woo product ID')
    woo_variation_id = fields.Char(string='Woo variation ID')
    woo_sku = fields.Char(string='SKU Woo')
    woo_name = fields.Char(string='Nombre Woo')
    order_status = fields.Char(string='Estado pedido')

    box_qty = fields.Float(string='Cajas vendidas', required=True, default=0.0)
    package_qty = fields.Integer(
        string='Pruebas por caja',
        related='presentation_id.package_qty',
        store=True,
        readonly=True,
    )
    piece_qty = fields.Float(
        string='Piezas vendidas',
        compute='_compute_piece_qty',
        store=True,
    )

    @api.depends('box_qty', 'presentation_id.package_qty')
    def _compute_piece_qty(self):
        for rec in self:
            rec.piece_qty = (rec.box_qty or 0.0) * (rec.presentation_id.package_qty or 0)

    @api.constrains('box_qty')
    def _check_box_qty(self):
        for rec in self:
            if rec.box_qty < 0:
                raise ValidationError(_('La cantidad vendida no puede ser negativa.'))

    @api.model
    def import_aggregated_row(self, values):
        """Import one read-only Woo sales aggregate.

        Expected keys: product/default_code, package_qty, sale_date, box_qty,
        optional Woo ids/SKU/name/status. The caller is responsible for
        filtering cancelled/caducidad/cortesia/capacitacion records.
        """
        product = values.get('product_id') and self.env['product.product'].browse(values['product_id'])
        if not product:
            sku = (values.get('odoo_sku') or values.get('woo_sku') or '').strip()
            product = self.env['product.product'].search([('default_code', '=', sku)], limit=1)
        if not product:
            raise ValidationError(_('No se encontro producto Odoo para SKU %s.') % (values.get('odoo_sku') or values.get('woo_sku') or ''))

        presentation = values.get('presentation_id') and self.env['amunet.packaging.presentation'].browse(values['presentation_id'])
        if not presentation:
            presentation = self.env['amunet.packaging.presentation'].find_or_create_from_woo(product, {
                'package_qty': values.get('package_qty'),
                'woo_product_id': values.get('woo_product_id'),
                'woo_variation_id': values.get('woo_variation_id'),
                'woo_sku': values.get('woo_sku'),
                'woo_name': values.get('woo_name'),
                'name': values.get('presentation_name'),
                'attribute_text': values.get('attribute_text'),
            })

        return self.create({
            'sale_date': values['sale_date'],
            'source': values.get('source') or 'woocommerce',
            'product_tmpl_id': product.product_tmpl_id.id,
            'product_id': product.id,
            'presentation_id': presentation.id,
            'woo_order_id': values.get('woo_order_id') or '',
            'woo_product_id': str(values.get('woo_product_id') or ''),
            'woo_variation_id': str(values.get('woo_variation_id') or ''),
            'woo_sku': values.get('woo_sku') or product.default_code,
            'woo_name': values.get('woo_name') or '',
            'order_status': values.get('order_status') or '',
            'box_qty': values.get('box_qty') or 0.0,
        })
