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
                                   string='Almacen', store=True, index=True)

    product_id = fields.Many2one(
        'product.product', string='Producto', required=True,
        domain="[('is_storable', '=', True)]",
        index=True,
    )
    uom_id = fields.Many2one(
        'uom.uom', string='UdM',
        related='product_id.uom_id', store=True, readonly=True,
        # readonly=True (no readonly=False): si fuera editable, al
        # ejecutar self.uom_id = product.uom_id en el onchange Odoo
        # intentaria propagar el valor de regreso al producto, lo cual
        # falla para usuarios sin write en product.product (cualquier
        # solicitante normal). La UdM SIEMPRE viene del producto, asi
        # que mantener readonly es lo correcto.
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
        index=True,
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
        # Campos que el almacenista puede editar EN LINEAS EXISTENTES
        # durante 'in_picking' (al surtir): asignar lote y capturar
        # cantidad surtida.
        warehouse_write_fields = {'lot_id', 'qty_supplied'}
        reception_fields = {'qty_received', 'line_reception_note'}
        user = self.env.user
        is_warehouse = self._is_material_warehouse()
        # vals vacio = la llamada viene del create() (despues de
        # super().create()), donde el modelo aun no recibe write
        # individual.
        is_create_call = not vals and not unlink

        for line in self:
            request = line.request_id
            if request.state == 'draft' and request.requester_id == user:
                continue
            # Almacenista: en borrador puede corregir libremente. Una vez
            # firmada por el solicitante, solo captura surtido operativo
            # (lote/cantidad surtida); no cambia producto ni cantidad pedida.
            if (
                is_warehouse
                and request.state == 'draft'
            ):
                continue
            # Almacenista: durante el surtido (in_picking) puede AGREGAR
            # lineas nuevas para material extra que realmente surtio. La
            # pantalla ya lo permite; aqui se habilita el backend. NO puede
            # cambiar producto/cantidad de lineas YA existentes: eso lo
            # cubre la rama de write de abajo (warehouse_write_fields).
            if (
                is_warehouse
                and request.state == 'in_picking'
                and is_create_call
            ):
                continue
            if (
                is_warehouse
                and request.state in ('submitted', 'in_picking')
                and not unlink
                and not is_create_call
                and set(vals).issubset(warehouse_write_fields)
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
        lines = self.filtered(lambda line: line.product_id and line.request_id.warehouse_id)
        for line in self - lines:
            line.stock_available = 0.0

        product_ids = lines.mapped('product_id').ids
        warehouse_ids = lines.mapped('request_id.warehouse_id').ids
        locations = self.env['stock.location'].search([
            ('warehouse_id', 'in', warehouse_ids),
            ('usage', '=', 'internal'),
        ])
        warehouse_by_location = {
            location.id: location.warehouse_id.id for location in locations
        }
        totals = {}
        if locations:
            grouped = self.env['stock.quant'].read_group(
                [
                    ('product_id', 'in', product_ids),
                    ('location_id', 'in', locations.ids),
                ],
                ['product_id', 'location_id', 'quantity:sum', 'reserved_quantity:sum'],
                ['product_id', 'location_id'],
                lazy=False,
            )
            for row in grouped:
                product = row.get('product_id')
                location = row.get('location_id')
                if not product or not location:
                    continue
                warehouse_id = warehouse_by_location.get(location[0])
                if not warehouse_id:
                    continue
                key = (product[0], warehouse_id)
                totals[key] = totals.get(key, 0.0) + (
                    row.get('quantity', 0.0) - row.get('reserved_quantity', 0.0)
                )

        for line in self:
            key = (line.product_id.id, line.request_id.warehouse_id.id)
            line.stock_available = totals.get(key, 0.0)

    @api.depends('lot_id', 'request_id.warehouse_id', 'request_id.picking_id')
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
            total_qty = sum(quants.mapped('quantity'))
            total_reserved = sum(quants.mapped('reserved_quantity'))
            # Sumar de vuelta la reserva del propio picking de esta
            # solicitud: cuando action_start_picking creo el picking,
            # este reservo qty_supplied del mismo lote. Sin esto, el
            # cierre falla pidiendo stock que ya esta apartado para
            # esa misma solicitud (caso reportado 2026-05-26 en
            # SMP/26/00024).
            own_picking = line.request_id.picking_id
            own_reserved = 0.0
            if own_picking and own_picking.state not in ('done', 'cancel'):
                own_reserved = sum(
                    ml.quantity
                    for ml in own_picking.move_line_ids
                    if ml.lot_id == line.lot_id
                )
            line.lot_available_qty = total_qty - total_reserved + own_reserved

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            # uom_id se actualiza automaticamente porque es related
            # store. Evitamos asignarlo explicitamente para no disparar
            # un write back al producto.
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
