# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class AmunetWooCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.env.user.group_ids |= cls.env.ref(
            'amunet_woocommerce.group_woo_admin')
        cls.Mapping = cls.env['amunet.woo.product.mapping']
        cls.backend = cls.env['amunet.woo.backend'].create({
            'name': 'Woo test (solo lectura)',
            'store_url': 'https://woo.example.test',
        })
        cls.location_stock = cls.env.ref('stock.stock_location_stock')
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.manu_type = cls.warehouse.manu_type_id
        if not cls.manu_type:
            cls.manu_type = cls.env['stock.picking.type'].create({
                'name': 'Manufacturing Woo Test',
                'code': 'mrp_operation',
                'sequence_code': 'MWT',
                'warehouse_id': cls.warehouse.id,
                'default_location_src_id': cls.location_stock.id,
                'default_location_dest_id': cls.location_stock.id,
            })
        if not cls.manu_type.default_location_src_id:
            cls.manu_type.default_location_src_id = cls.location_stock.id

    def _make_product(self, name, code):
        # amunet_warehouse_access bloquea el alta de productos por procesos
        # automaticos salvo alta EXPLICITA autorizada; las pruebas son ese
        # caso, asi que usan el flag de contexto que el propio candado define.
        return self.env['product.product'].with_context(
            amunet_alta_autorizada=True).create({
            'name': name,
            'default_code': code,
            'type': 'consu',
            'is_storable': True,
        })

    def _make_bom(self, product, components):
        """components: lista de (producto componente, cantidad por BOM)."""
        return self.env['mrp.bom'].create({
            'product_tmpl_id': product.product_tmpl_id.id,
            'product_qty': 1.0,
            'picking_type_id': self.manu_type.id,
            'bom_line_ids': [
                (0, 0, {'product_id': comp.id, 'product_qty': qty})
                for comp, qty in components
            ],
        })

    def _add_stock(self, product, qty, location=None):
        self.env['stock.quant']._update_available_quantity(
            product, location or self.location_stock, qty)

    def _make_mapping(self, product, woo_id, **extra):
        values = {
            'backend_id': self.backend.id,
            'product_id': product.id,
            'woo_product_id': woo_id,
            'woo_sku': product.default_code,
            'woo_name': product.name,
        }
        values.update(extra)
        return self.Mapping.create(values)
