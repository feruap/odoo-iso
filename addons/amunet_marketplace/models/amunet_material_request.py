from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AmunetMaterialRequest(models.Model):
    _inherit = 'amunet.material.request'

    request_type = fields.Selection(
        selection=[
            ('general', 'Compra general'),
            ('production', 'Produccion / fabricacion'),
        ],
        string='Tipo de solicitud',
        default='general',
        required=True,
        tracking=True,
    )
    mrp_production_id = fields.Many2one(
        'mrp.production',
        string='Orden de fabricacion',
        tracking=True,
        help='Usar cuando la solicitud este ligada a una orden de fabricacion.',
    )
    marketplace_source_product_tmpl_id = fields.Many2one(
        'product.template',
        string='Producto origen marketplace',
        readonly=True,
        copy=False,
    )
    product_proposal_id = fields.Many2one(
        'amunet.marketplace.product.proposal',
        string='Propuesta de producto',
        readonly=True,
        copy=False,
    )

    @api.constrains('request_type', 'mrp_production_id')
    def _check_request_type_links(self):
        for rec in self:
            if rec.request_type == 'production' and not rec.mrp_production_id:
                raise UserError(_(
                    'Las solicitudes de tipo Produccion / fabricacion deben indicar una orden de fabricacion.'
                ))


class AmunetMaterialRequestLine(models.Model):
    _inherit = 'amunet.material.request.line'

    @api.constrains('product_id', 'request_id.request_type')
    def _check_marketplace_product_flow(self):
        for line in self:
            product = line.product_id.product_tmpl_id
            if not product.marketplace_enabled:
                continue
            if line.request_id.request_type == 'general' and product.marketplace_flow == 'production':
                raise UserError(_(
                    'El producto %s esta configurado solo para solicitudes de produccion.'
                ) % product.display_name)
            if line.request_id.request_type == 'production' and product.marketplace_flow == 'general':
                raise UserError(_(
                    'El producto %s esta configurado solo para solicitudes generales.'
                ) % product.display_name)

