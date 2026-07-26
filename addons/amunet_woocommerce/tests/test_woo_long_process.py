# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError

from .common import AmunetWooCommon


class TestWooLongProcess(AmunetWooCommon):

    def setUp(self):
        super().setUp()
        self.component = self._make_product('Insumo hoja', 'INHM01')
        self.master = self._make_product('Hoja maestra', 'HMTEST01')
        self.final = self._make_product('Producto final largo', 'PTLONG01')
        self.bom = self._make_bom(self.master, [(self.component, 2.0)])
        self._add_stock(self.component, 20.0)   # 10 hojas potenciales
        self._add_stock(self.master, 10.0)      # 10 hojas físicas

    def _make_profile(self, **extra):
        values = {
            'name': 'Perfil largo test',
            'product_id': self.final.id,
            'master_product_id': self.master.id,
            'bom_id': self.bom.id,
        }
        values.update(extra)
        return self.env['amunet.woo.long.process'].create(values)

    def test_pieces_equivalence_with_yield_and_scrap(self):
        profile = self._make_profile(
            equivalence_type='pieces', pieces_per_sheet=100.0,
            yield_percent=80.0, scrap_percent=50.0)
        self.env.invalidate_all()
        # Factor ajustado: 100 * 0.8 * 0.5 = 40 piezas por hoja.
        self.assertTrue(profile.master_stock_calculable)
        self.assertTrue(profile.master_physical_calculable)
        self.assertEqual(profile.master_qty_physical, 10.0)
        self.assertTrue(profile.potential_sheets_calculable)
        self.assertEqual(profile.potential_sheets_from_bom, 10.0)
        self.assertTrue(profile.pieces_calculable)
        self.assertEqual(profile.pieces_from_physical, 400.0)
        self.assertEqual(profile.pieces_from_bom, 400.0)
        self.assertEqual(profile.pieces_total_potential, 800.0)

    def test_cm_equivalence(self):
        profile = self._make_profile(
            equivalence_type='cm', usable_cm_per_sheet=50.0,
            pieces_per_cm=2.0, yield_percent=100.0, scrap_percent=0.0)
        self.env.invalidate_all()
        # Factor: 50 cm * 2 piezas/cm = 100 piezas por hoja.
        self.assertTrue(profile.pieces_calculable)
        self.assertEqual(profile.pieces_from_physical, 1000.0)
        self.assertEqual(profile.pieces_total_potential, 2000.0)

    def test_pieces_not_calculable_without_equivalence(self):
        profile = self._make_profile(
            equivalence_type='pieces', pieces_per_sheet=0.0)
        self.env.invalidate_all()
        self.assertFalse(profile.pieces_calculable)
        self.assertTrue(profile.pieces_reason)

    def test_pieces_not_calculable_without_bom(self):
        profile = self._make_profile(bom_id=False, pieces_per_sheet=100.0)
        self.env.invalidate_all()
        self.assertFalse(profile.potential_sheets_calculable)
        self.assertTrue(profile.potential_sheets_reason)
        self.assertFalse(profile.pieces_calculable)

    def test_quality_release_without_regulatory_field(self):
        if 'amunet_lot_release_state' in self.env['stock.lot']._fields:
            self.skipTest('amunet_quality instalado: el campo existe')
        profile = self._make_profile(
            pieces_per_sheet=100.0, quality_release_required=True)
        self.env.invalidate_all()
        # Dato de liberación ausente: jamás se convierte en cero.
        self.assertFalse(profile.master_stock_calculable)
        self.assertTrue(profile.master_physical_calculable)
        self.assertEqual(profile.master_qty_physical, 10.0)
        self.assertFalse(profile.master_released_calculable)
        self.assertTrue(profile.master_stock_reason)
        self.assertFalse(profile.pieces_calculable)

    def test_range_constraints(self):
        profile = self._make_profile()
        with self.assertRaises(ValidationError):
            profile.write({'yield_percent': 150.0})
        with self.assertRaises(ValidationError):
            profile.write({'yield_percent': -1.0})
        with self.assertRaises(ValidationError):
            profile.write({'scrap_percent': 120.0})
        with self.assertRaises(ValidationError):
            profile.write({'scrap_percent': 100.0})
        with self.assertRaises(ValidationError):
            profile.write({'scrap_percent': -5.0})
        with self.assertRaises(ValidationError):
            profile.write({'pieces_per_sheet': -2.0})

    def test_bom_must_produce_master_sheet(self):
        other = self._make_product('Otro producto', 'OTROHM01')
        other_bom = self._make_bom(other, [(self.component, 1.0)])
        with self.assertRaises(ValidationError):
            self._make_profile(bom_id=other_bom.id)
