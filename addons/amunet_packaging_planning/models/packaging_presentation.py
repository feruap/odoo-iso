# -*- coding: utf-8 -*-

import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AmunetPackagingPresentation(models.Model):
    _name = 'amunet.packaging.presentation'
    _description = 'Presentacion de empaque autorizada'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'product_tmpl_id, package_qty, name'

    name = fields.Char(string='Presentacion', required=True, tracking=True)
    active = fields.Boolean(default=True, tracking=True)

    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Producto maestro',
        required=True,
        tracking=True,
        help='Producto diagnostico al que pertenece esta presentacion.',
    )
    product_id = fields.Many2one(
        'product.product',
        string='Producto Odoo de venta/empaque',
        domain="[('product_tmpl_id', '=', product_tmpl_id)]",
        help='Opcional. Usarlo si la caja c/5, c/20, etc. existe como variante/producto en Odoo.',
    )
    package_qty = fields.Integer(
        string='Pruebas por caja',
        required=True,
        tracking=True,
    )
    woo_product_id = fields.Char(string='Woo product ID')
    woo_variation_id = fields.Char(string='Woo variation ID')
    woo_sku = fields.Char(string='SKU WooCommerce', tracking=True)
    woo_name = fields.Char(string='Nombre WooCommerce')

    authorization_source = fields.Selection([
        ('woocommerce', 'WooCommerce publicado'),
        ('odoo', 'Odoo / master data'),
        ('manual', 'Manual autorizado'),
        ('demo', 'Demo / pendiente confirmar'),
    ], string='Fuente autorizacion', default='manual', required=True, tracking=True)
    is_authorized = fields.Boolean(
        string='Autorizada para uso',
        default=True,
        tracking=True,
        help='Si esta desmarcado, no puede usarse para planear empaque ni reacondicionar.',
    )

    box_component_id = fields.Many2one('product.product', string='Caja / funda')
    label_component_id = fields.Many2one('product.product', string='Etiqueta')
    manual_component_id = fields.Many2one('product.product', string='Manual / instructivo')
    label_required = fields.Boolean(string='Requiere etiqueta', default=True)
    manual_required = fields.Boolean(string='Requiere manual', default=True)

    trend_line_ids = fields.One2many(
        'amunet.woo.sales.trend',
        'presentation_id',
        string='Tendencia Woo',
    )
    trend_piece_qty_180 = fields.Float(
        string='Piezas vendidas 180d',
        compute='_compute_trend_totals',
    )
    trend_box_qty_180 = fields.Float(
        string='Cajas vendidas 180d',
        compute='_compute_trend_totals',
    )
    last_trend_date = fields.Date(
        string='Ultima venta Woo',
        compute='_compute_trend_totals',
    )

    @api.depends('trend_line_ids.sale_date', 'trend_line_ids.box_qty', 'trend_line_ids.piece_qty')
    def _compute_trend_totals(self):
        today = fields.Date.context_today(self)
        for rec in self:
            date_from = fields.Date.subtract(today, days=180)
            lines = rec.trend_line_ids.filtered(
                lambda line: line.sale_date and line.sale_date >= date_from
            )
            rec.trend_box_qty_180 = sum(lines.mapped('box_qty'))
            rec.trend_piece_qty_180 = sum(lines.mapped('piece_qty'))
            dates = lines.mapped('sale_date')
            rec.last_trend_date = max(dates) if dates else False

    @api.constrains('package_qty')
    def _check_package_qty(self):
        for rec in self:
            if rec.package_qty <= 0:
                raise ValidationError(_('Las pruebas por caja deben ser mayores a cero.'))

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.product_tmpl_id = rec.product_id.product_tmpl_id
                if not rec.woo_sku and rec.product_id.default_code:
                    rec.woo_sku = rec.product_id.default_code

    @api.model
    def infer_package_qty(self, text):
        text = str(text or '')
        patterns = [
            r'(?:caja|tubo|bolsa)\s*(?:con|c/|de)?\s*(\d{1,4})\s*(?:prueba|pruebas|tira|tiras|pieza|piezas)',
            r'(?:c/|c\s*/\s*)(\d{1,4})',
            r'(\d{1,4})\s*(?:prueba|pruebas|tira|tiras|pieza|piezas)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.I)
            if match:
                return int(match.group(1))
        return 0

    @api.model
    def find_or_create_from_woo(self, product, woo_values):
        """Create/update the authorized presentation detected from WooCommerce.

        Woo remains the source for what is saleable, but the presentation still
        needs to be explicitly authorized before it can be used in production.
        """
        qty = int(woo_values.get('package_qty') or 0)
        if not qty:
            qty = self.infer_package_qty(
                ' '.join([
                    woo_values.get('woo_name') or '',
                    woo_values.get('woo_sku') or '',
                    woo_values.get('attribute_text') or '',
                ])
            )
        if not qty:
            qty = 1

        product_tmpl = product.product_tmpl_id
        domain = [
            ('product_tmpl_id', '=', product_tmpl.id),
            ('package_qty', '=', qty),
        ]
        if woo_values.get('woo_variation_id'):
            domain = [('woo_variation_id', '=', str(woo_values['woo_variation_id']))]
        elif woo_values.get('woo_sku'):
            domain += [('woo_sku', '=', woo_values['woo_sku'])]

        rec = self.search(domain, limit=1)
        vals = {
            'name': woo_values.get('name') or ('Caja c/%s' % qty),
            'product_tmpl_id': product_tmpl.id,
            'product_id': product.id,
            'package_qty': qty,
            'woo_product_id': str(woo_values.get('woo_product_id') or ''),
            'woo_variation_id': str(woo_values.get('woo_variation_id') or ''),
            'woo_sku': woo_values.get('woo_sku') or product.default_code,
            'woo_name': woo_values.get('woo_name') or '',
            'authorization_source': 'woocommerce',
            'is_authorized': True,
        }
        if rec:
            rec.write(vals)
        else:
            rec = self.create(vals)
        return rec
