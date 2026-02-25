# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # Campos para BOM Transfer
    use_bom_transfer = fields.Boolean(
        string='Entrega por lista de materiales',
        default=False,
        help='Activar para usar lista de materiales y generar componentes automáticamente'
    )
    bom_product_id = fields.Many2one(
        'product.product',
        string='Producto con lista de materiales',
        domain="[('id', 'in', available_bom_product_ids)]",
        help='Seleccione el producto que tiene configurada una lista de materiales'
    )
    bom_product_qty = fields.Float(
        string='Cantidad',
        default=1.0,
        digits='Product Unit of Measure',
        help='Cantidad de productos a entregar'
    )
    available_bom_product_ids = fields.Many2many(
        'product.product',
        compute='_compute_available_bom_products',
        string='Productos con BOM Disponibles'
    )

    # Campo computado para controlar visibilidad en UI
    show_bom_fields = fields.Boolean(
        compute='_compute_show_bom_fields',
        string='Mostrar campos BOM'
    )

    @api.depends('picking_type_id', 'picking_type_id.enable_bom_transfer',
                 'picking_type_id.code')
    def _compute_show_bom_fields(self):
        """Mostrar campos BOM solo si es entrega y está habilitado"""
        for picking in self:
            if picking.picking_type_id:
                picking.show_bom_fields = (
                    picking.picking_type_id.code == 'outgoing' and
                    picking.picking_type_id.enable_bom_transfer
                )
            else:
                picking.show_bom_fields = False

    @api.depends('company_id')
    def _compute_available_bom_products(self):
        """Obtener productos que tienen BOM configurado"""
        for picking in self:
            boms = self.env['amunet.transfer.bom'].search([
                ('company_id', '=', picking.company_id.id),
                ('active', '=', True)
            ])
            picking.available_bom_product_ids = boms.mapped('product_id')

    @api.onchange('use_bom_transfer', 'bom_product_id', 'bom_product_qty', 'location_id', 'location_dest_id')
    def _onchange_bom_product(self):
        """Cuando cambie producto o cantidad, regenerar move_ids"""
        # Si se desactiva el toggle, no hacer nada (las líneas permanecen según AC6)
        if not self.use_bom_transfer:
            return

        # Validar que tenemos los datos necesarios
        if not self.bom_product_id or not self.bom_product_qty or self.bom_product_qty <= 0:
            return

        # Solo procesar si el picking está en estado draft o es nuevo
        if self.state and self.state != 'draft':
            return

        # Buscar BOM para el producto
        bom = self.env['amunet.transfer.bom'].search([
            ('product_id', '=', self.bom_product_id.id),
            ('company_id', '=', self.company_id.id if self.company_id else self.env.company.id),
            ('active', '=', True)
        ], limit=1)

        if not bom:
            return {'warning': {
                'title': 'Lista de materiales no encontrada',
                'message': f'No se encontró una lista de materiales activa para el producto {self.bom_product_id.display_name}.'
            }}

        if not bom.bom_line_ids:
            return {'warning': {
                'title': 'Lista de materiales vacía',
                'message': f'La lista de materiales para {self.bom_product_id.display_name} no tiene componentes configurados.'
            }}

        # Calcular factor de multiplicación
        factor = self.bom_product_qty / bom.product_qty if bom.product_qty > 0 else 1.0

        # Obtener ubicaciones (usar las del picking o las del tipo de operación)
        location_id = self.location_id.id if self.location_id else (
            self.picking_type_id.default_location_src_id.id if self.picking_type_id and self.picking_type_id.default_location_src_id else False
        )
        location_dest_id = self.location_dest_id.id if self.location_dest_id else (
            self.picking_type_id.default_location_dest_id.id if self.picking_type_id and self.picking_type_id.default_location_dest_id else False
        )

        if not location_id or not location_dest_id:
            return {'warning': {
                'title': 'Ubicaciones no configuradas',
                'message': 'Debe configurar las ubicaciones origen y destino antes de generar las líneas de componentes.'
            }}

        # Preparar comandos para modificar move_ids
        # Eliminar todas las líneas existentes y crear nuevas
        commands = [(5, 0, 0)]  # Eliminar todas las líneas (guardadas y no guardadas)

        # Generar nuevas líneas de movimiento basadas en el BOM
        for bom_line in bom.bom_line_ids:
            if not bom_line.product_id:
                continue

            qty = bom_line.product_qty * factor

            move_vals = {
                'product_id': bom_line.product_id.id,
                'product_uom_qty': qty,
                'product_uom': (
                    bom_line.product_uom_id.id
                    if bom_line.product_uom_id
                    else bom_line.product_id.uom_id.id
                ),
                'location_id': location_id,
                'location_dest_id': location_dest_id,
            }
            # picking_id se establece automáticamente por Odoo al asignar a move_ids
            commands.append((0, 0, move_vals))

        # Aplicar cambios solo si hay líneas para crear
        if len(commands) > 1:  # Más que solo la eliminación
            self.move_ids = commands
