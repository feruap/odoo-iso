from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AmunetMaterialRequestLine(models.Model):
    _name = 'amunet.material.request.line'
    _description = 'Linea de Solicitud de Material'

    request_id = fields.Many2one(
        'amunet.material.request', string='Solicitud',
        ondelete='cascade', required=True, index=True,
    )
    state = fields.Selection(related='request_id.state', store=True, string='Estado')
    warehouse_id = fields.Many2one(related='request_id.warehouse_id',
                                   string='Almacen', store=True)

    product_id = fields.Many2one(
        'product.product', string='Producto', required=True,
        domain="[('is_storable', '=', True)]",
    )
    uom_id = fields.Many2one(
        'uom.uom', string='UdM',
        related='product_id.uom_id', store=True, readonly=False,
    )
    tracking = fields.Selection(related='product_id.tracking', store=True,
                                string='Trazabilidad')

    qty_requested = fields.Float(string='Cantidad solicitada', default=1.0,
                                 digits='Product Unit of Measure')
    qty_supplied = fields.Float(string='Cantidad surtida', default=0.0,
                                digits='Product Unit of Measure')

    lot_id = fields.Many2one(
        'stock.lot', string='Lote',
        domain="[('product_id', '=', product_id)]",
    )

    stock_available = fields.Float(
        string='Stock disponible',
        compute='_compute_stock_available',
        digits='Product Unit of Measure',
    )
    lot_available_qty = fields.Float(
        string='Disponible en lote',
        compute='_compute_lot_available_qty',
        digits='Product Unit of Measure',
    )

    # Validacion de recepcion: el solicitante (o su jefe) confirma cuanto
    # recibio realmente de cada producto. Editable solo en estado
    # pending_reception y por quien puede validar.
    qty_received = fields.Float(
        string='Cantidad recibida', default=0.0,
        digits='Product Unit of Measure',
    )
    line_reception_note = fields.Char(
        string='Observacion recepcion',
        help='Por ejemplo: "Llegaron 8 de 10", "Caja danada", etc.',
    )
    reception_status = fields.Selection(
        selection=[
            ('none', 'Sin validar'),
            ('complete', 'Completa'),
            ('partial', 'Parcial'),
        ],
        string='Estado recepcion',
        compute='_compute_reception_status', store=True,
    )

    def _is_material_manager(self):
        return self.env.user.has_group(
            'amunet_material_request.group_material_manager')

    def _is_material_warehouse(self):
        return self.env.user.has_group(
            'amunet_material_request.group_material_warehouse')

    def _check_can_modify_line(self, vals=None, unlink=False):
        if self.env.context.get('material_request_internal_write'):
            return
        if self._is_material_manager():
            return

        vals = vals or {}
        warehouse_fields = {'lot_id', 'qty_supplied'}
        reception_fields = {'qty_received', 'line_reception_note'}
        user = self.env.user

        for line in self:
            request = line.request_id
            if request.state == 'draft' and request.requester_id == user:
                continue
            if (
                not unlink
                and self._is_material_warehouse()
                and request.state == 'in_picking'
                and set(vals).issubset(warehouse_fields)
            ):
                continue
            # Validador (solicitante o jefe de area) en pending_reception
            # puede modificar solo los campos de recepcion.
            if (
                not unlink
                and request.state == 'pending_reception'
                and set(vals).issubset(reception_fields)
                and request.can_validate_reception
            ):
                continue
            raise UserError(_(
                'No puedes modificar lineas de la solicitud %s en este '
                'estado o con tu rol.') % request.name)

    @api.depends('qty_supplied', 'qty_received')
    def _compute_reception_status(self):
        for line in self:
            if line.qty_received <= 0:
                line.reception_status = 'none'
            elif line.qty_received >= line.qty_supplied:
                line.reception_status = 'complete'
            else:
                line.reception_status = 'partial'

    @api.depends('product_id', 'request_id.warehouse_id')
    def _compute_stock_available(self):
        for line in self:
            if not line.product_id or not line.request_id.warehouse_id:
                line.stock_available = 0.0
                continue
            quants = self.env['stock.quant'].search([
                ('product_id', '=', line.product_id.id),
                ('location_id.warehouse_id', '=', line.request_id.warehouse_id.id),
                ('location_id.usage', '=', 'internal'),
            ])
            line.stock_available = sum(quants.mapped('quantity')) - sum(quants.mapped('reserved_quantity'))

    @api.depends('lot_id', 'request_id.warehouse_id')
    def _compute_lot_available_qty(self):
        for line in self:
            if not line.lot_id or not line.request_id.warehouse_id:
                line.lot_available_qty = 0.0
                continue
            quants = self.env['stock.quant'].search([
                ('lot_id', '=', line.lot_id.id),
                ('location_id.warehouse_id', '=', line.request_id.warehouse_id.id),
                ('location_id.usage', '=', 'internal'),
            ])
            line.lot_available_qty = sum(quants.mapped('quantity')) - sum(quants.mapped('reserved_quantity'))

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id.id
            self.lot_id = False
            self.qty_supplied = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._check_can_modify_line()
        return lines

    def write(self, vals):
        self._check_can_modify_line(vals=vals)
        return super().write(vals)

    def unlink(self):
        self._check_can_modify_line(unlink=True)
        return super().unlink()
