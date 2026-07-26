# -*- coding: utf-8 -*-

from .common import AmunetWooCommon


class TestWooCapacity(AmunetWooCommon):

    def test_short_capacity_valid(self):
        component = self._make_product('Componente A', 'COMPA01')
        final = self._make_product('Final A', 'FINA01')
        self._make_bom(final, [(component, 2.0)])
        self._add_stock(component, 10.0)
        mapping = self._make_mapping(
            final, 600001, supply_classification='short_manufacturing')
        self.env.invalidate_all()
        self.assertTrue(mapping.short_capacity_calculable)
        self.assertFalse(mapping.short_capacity_reason)
        # 10 unidades de componente / 2 por BOM = 5 unidades fabricables.
        self.assertEqual(mapping.short_capacity_qty, 5.0)

    def test_short_capacity_zero_is_valid_when_configured(self):
        component = self._make_product('Componente B', 'COMPB01')
        final = self._make_product('Final B', 'FINB01')
        self._make_bom(final, [(component, 4.0)])
        # Sin existencias: todo está configurado, cero sí es resultado válido.
        mapping = self._make_mapping(
            final, 600002, supply_classification='short_manufacturing')
        self.env.invalidate_all()
        self.assertTrue(mapping.short_capacity_calculable)
        self.assertEqual(mapping.short_capacity_qty, 0.0)

    def test_negative_free_stock_never_creates_negative_capacity(self):
        component = self._make_product('Componente negativo', 'COMPNEG01')
        final = self._make_product('Final stock negativo', 'FINNEG01')
        self._make_bom(final, [(component, 2.0)])
        self._add_stock(component, -6.0)
        mapping = self._make_mapping(
            final, 600012, supply_classification='short_manufacturing')
        self.env.invalidate_all()
        self.assertTrue(mapping.short_capacity_calculable)
        self.assertEqual(mapping.short_capacity_qty, 0.0)

    def test_repeated_component_lines_do_not_double_count_stock(self):
        component = self._make_product('Componente repetido', 'COMPREP01')
        final = self._make_product('Final repetido', 'FINREP01')
        self._make_bom(final, [(component, 2.0), (component, 3.0)])
        self._add_stock(component, 10.0)
        mapping = self._make_mapping(
            final, 600010, supply_classification='short_manufacturing')
        self.env.invalidate_all()
        self.assertTrue(mapping.short_capacity_calculable)
        # Se requieren 5 componentes por producto, no dos bolsas separadas de
        # inventario: 10 / (2 + 3) = 2.
        self.assertEqual(mapping.short_capacity_qty, 2.0)

    def test_not_calculable_without_bom(self):
        final = self._make_product('Final sin BOM', 'SINBOM01')
        mapping = self._make_mapping(
            final, 600003, supply_classification='short_manufacturing')
        self.assertFalse(mapping.short_capacity_calculable)
        self.assertTrue(mapping.short_capacity_reason)
        self.assertTrue(mapping.any_not_calculable)

    def test_not_calculable_without_snapshot(self):
        final = self._make_product('Final sin snapshot', 'SINSNAP01')
        mapping = self._make_mapping(final, 600004)
        self.assertFalse(mapping.woo_inventory_calculable)
        self.assertTrue(mapping.woo_inventory_reason)
        self.assertFalse(mapping.last_snapshot_date)

    def test_snapshot_makes_woo_inventory_calculable(self):
        final = self._make_product('Final con snapshot', 'CONSNAP01')
        mapping = self._make_mapping(final, 600005)
        self.env['amunet.woo.stock.snapshot'].create({
            'mapping_id': mapping.id,
            'source': 'manual',
            'available_known': True,
            'qty_available': 12.0,
            'reserved_known': True,
            'qty_reserved': 3.0,
            'expired_known': True,
            'damaged_known': True,
        })
        self.env.invalidate_all()
        self.assertTrue(mapping.woo_inventory_calculable)
        self.assertEqual(mapping.woo_qty_available, 12.0)
        self.assertEqual(mapping.woo_qty_reserved, 3.0)
        self.assertFalse(mapping.snapshot_stale)

    def test_partial_snapshot_does_not_invent_zeros(self):
        final = self._make_product('Final snapshot parcial', 'SNAPPAR01')
        mapping = self._make_mapping(final, 600008)
        self.env['amunet.woo.stock.snapshot'].create({
            'mapping_id': mapping.id,
            'source': 'manual',
            'available_known': True,
            'qty_available': 0.0,
        })
        self.env.invalidate_all()
        self.assertEqual(mapping.woo_available_display, '0')
        self.assertEqual(mapping.woo_reserved_display, 'No calculable')
        self.assertFalse(mapping.woo_inventory_calculable)

    def test_lot_release_not_calculable_without_quality_field(self):
        if 'amunet_lot_release_state' in self.env['stock.lot']._fields:
            self.skipTest('amunet_quality instalado: el campo existe')
        final = self._make_product('Final lotes', 'LOTES01')
        mapping = self._make_mapping(final, 600006)
        self.assertFalse(mapping.lot_release_calculable)
        self.assertTrue(mapping.lot_release_reason)

    def test_odoo_inventory_read_only_values(self):
        final = self._make_product('Final inventario', 'INV01')
        self._add_stock(final, 7.0)
        mapping = self._make_mapping(final, 600007)
        self.env.invalidate_all()
        self.assertEqual(mapping.odoo_qty_onhand, 7.0)
        self.assertEqual(mapping.odoo_qty_free, 7.0)

    def test_bom_and_packaging_phase_are_visible_without_classification(self):
        component = self._make_product('Componente visible', 'BOMVISCOMP01')
        final = self._make_product('Final BOM visible', 'BOMVISFIN01')
        self._make_bom(final, [(component, 1.0)])
        mapping = self._make_mapping(final, 600009)
        self.env.invalidate_all()
        self.assertTrue(mapping.has_active_bom)
        self.assertEqual(mapping.active_bom_count, 1)
        self.assertIn('BOM activa', mapping.bom_status_display)
        self.assertTrue(mapping.packaging_calculable)
        self.assertEqual(mapping.packaging_plan_count, 0)
        self.assertEqual(mapping.packaging_display, '0')

    def test_approved_packaging_zero_is_not_replaced_by_theoretical_qty(self):
        final = self._make_product('Final empaque cero', 'EMPAQZERO01')
        production = self.env['mrp.production'].create({
            'product_id': final.id,
            'product_qty': 12.0,
            'product_uom_id': final.uom_id.id,
            'picking_type_id': self.manu_type.id,
            'location_src_id': self.location_stock.id,
            'location_dest_id': self.location_stock.id,
        })
        self.env['amunet.packaging.plan'].create({
            'production_id': production.id,
            'state': 'approved',
        })
        mapping = self._make_mapping(final, 600011)
        self.env.invalidate_all()
        self.assertTrue(mapping.packaging_calculable)
        self.assertEqual(mapping.packaging_plan_count, 1)
        self.assertEqual(mapping.packaging_planned_qty, 0.0)
        self.assertEqual(mapping.packaging_display, '0')
