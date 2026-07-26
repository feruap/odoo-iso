from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    marketplace_enabled = fields.Boolean(
        string='Visible en marketplace',
        help='Si esta activo, el producto aparece en el catalogo interno.',
    )
    marketplace_flow = fields.Selection(
        selection=[
            ('general', 'Compra general'),
            ('production', 'Produccion / fabricacion'),
            ('both', 'Ambos'),
        ],
        string='Flujo marketplace',
        default='general',
        required=True,
        help='Define en que tipo de solicitud debe aparecer el producto.',
    )
    marketplace_sequence = fields.Integer(
        string='Secuencia marketplace',
        default=10,
    )
    marketplace_purchase_url = fields.Char(
        string='URL de referencia de compra',
        help='URL fuente del producto para compras o validacion de proveedor.',
    )
    marketplace_reference_price = fields.Float(
        string='Precio de referencia',
        help='Precio solo informativo para el catalogo interno.',
        digits='Product Price',
    )
    marketplace_request_note = fields.Text(
        string='Nota para solicitud',
        help='Indicaciones operativas visibles al usuario al pedir este producto.',
    )
    marketplace_requires_approval = fields.Boolean(
        string='Requiere autorizacion adicional',
        help='Marcador operativo para productos que deban revisarse antes de comprar o surtir.',
    )

    marketplace_display_type = fields.Selection(
        selection=[
            ('general', 'Compra general'),
            ('production', 'Produccion / fabricacion'),
            ('both', 'Ambos'),
        ],
        string='Uso visible',
        compute='_compute_marketplace_display_type',
    )

    @api.depends('marketplace_flow')
    def _compute_marketplace_display_type(self):
        for rec in self:
            rec.marketplace_display_type = rec.marketplace_flow or 'general'

    def action_open_marketplace_request(self):
        self.ensure_one()
        if not self.marketplace_enabled:
            raise UserError(_('Este producto no esta habilitado para el marketplace interno.'))
        product = self.product_variant_id
        if not product:
            raise UserError(_('El producto no tiene una variante utilizable para solicitud.'))
        request_type = 'production' if self.marketplace_flow == 'production' else 'general'
        if self.marketplace_flow == 'both':
            request_type = self.env.context.get('default_request_type') or 'general'
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nueva solicitud desde marketplace'),
            'res_model': 'amunet.material.request',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_request_type': request_type,
                'default_marketplace_source_product_tmpl_id': self.id,
                'default_note': self.marketplace_request_note or False,
                'default_line_ids': [
                    (0, 0, {
                        'product_id': product.id,
                        'qty_requested': 1.0,
                    })
                ],
            },
        }

