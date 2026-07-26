# -*- coding: utf-8 -*-

import base64

from odoo import fields

from .common import AmunetWooCommon

CSV_TEMPLATE = (
    'woo_id,woo_sku,titulo,piezas,odoo_default_code,odoo_track,odoo_use_exp,'
    'confianza,metodo,justificacion\n'
    '91234,INRPZ01-R,Caja con 96 puntas,8,WCTESTA01,,,alta,insumo IN->CO,just uno\n'
    '101620,EQCBV01-1,Centrifuga baja velocidad,1,WCTESTB01,lot,false,media,'
    'nombre(1.00),\n'
    '99999,NOPE01,Inexistente,1,NOEXISTE01,,,baja,prueba,\n'
    'abc,BAD01,Rota,1,WCTESTA01,,,alta,prueba,\n'
)


class TestWooMappingImport(AmunetWooCommon):

    def setUp(self):
        super().setUp()
        self.product_a = self._make_product('Puntas 100-1000uL', 'WCTESTA01')
        self.product_b = self._make_product('Centrifuga', 'WCTESTB01')

    def _run_wizard(
            self, content=CSV_TEMPLATE,
            snapshot_date='2026-07-24 07:30:01'):
        wizard = self.env['amunet.woo.mapping.import.wizard'].create({
            'backend_id': self.backend.id,
            'data_file': base64.b64encode(content.encode('utf-8')),
            'filename': 'mapeo_sku_woo_odoo.csv',
            'snapshot_date': fields.Datetime.to_datetime(snapshot_date),
        })
        wizard.action_import()
        return wizard

    def test_import_counts_and_values(self):
        wizard = self._run_wizard()
        self.assertEqual(wizard.created_count, 3)
        self.assertEqual(wizard.updated_count, 0)
        self.assertEqual(wizard.not_found_count, 1)
        self.assertEqual(wizard.error_count, 1)
        self.assertIn('NOEXISTE01', wizard.report)
        mapping = self.Mapping.search([
            ('backend_id', '=', self.backend.id),
            ('woo_product_id', '=', 91234),
        ])
        self.assertEqual(len(mapping), 1)
        self.assertEqual(mapping.product_id, self.product_a)
        self.assertEqual(mapping.relation_state, 'pending')
        self.assertEqual(mapping.confidence, 'high')
        self.assertEqual(mapping.match_method, 'insumo IN->CO')
        snapshot = mapping.snapshot_ids.filtered(
            lambda rec: rec.source == 'csv')
        self.assertEqual(len(snapshot), 1)
        self.assertTrue(snapshot.available_known)
        self.assertEqual(snapshot.qty_available, 8)
        self.assertFalse(snapshot.reserved_known)

    def test_import_is_idempotent(self):
        first = self._run_wizard()
        self.assertEqual(first.created_count, 3)
        second = self._run_wizard()
        self.assertEqual(second.created_count, 0)
        self.assertEqual(second.updated_count, 3)
        self.assertEqual(second.error_count, 1)
        self.assertEqual(
            self.Mapping.search_count([
                ('backend_id', '=', self.backend.id),
                ('woo_product_id', '=', 91234),
            ]), 1)
        self.assertEqual(
            self.Mapping.search_count([
                ('backend_id', '=', self.backend.id),
                ('woo_product_id', '=', 101620),
            ]), 1)
        mapping = self.Mapping.search([
            ('backend_id', '=', self.backend.id),
            ('woo_product_id', '=', 91234),
        ])
        self.assertEqual(
            len(mapping.snapshot_ids.filtered(lambda rec: rec.source == 'csv')),
            1)

    def test_new_observation_date_preserves_snapshot_history(self):
        self._run_wizard(snapshot_date='2026-07-24 07:30:01')
        self._run_wizard(snapshot_date='2026-07-25 07:30:01')
        mapping = self.Mapping.search([
            ('backend_id', '=', self.backend.id),
            ('woo_product_id', '=', 91234),
        ])
        snapshots = mapping.snapshot_ids.filtered(
            lambda rec: rec.source == 'csv')
        self.assertEqual(len(snapshots), 2)
        self.assertEqual(
            set(snapshots.mapped('date')),
            {
                fields.Datetime.to_datetime('2026-07-24 07:30:01'),
                fields.Datetime.to_datetime('2026-07-25 07:30:01'),
            },
        )

    def test_reimport_preserves_human_review(self):
        self._run_wizard()
        mapping = self.Mapping.search([
            ('backend_id', '=', self.backend.id),
            ('woo_product_id', '=', 91234),
        ])
        mapping.action_confirm()
        reviewer = mapping.reviewer_id
        review_date = mapping.review_date
        changed_csv = CSV_TEMPLATE.replace(
            '91234,INRPZ01-R,Caja con 96 puntas,8,WCTESTA01',
            '91234,INRPZ01-R,Título cambiado,9,NOEXISTE01',
        )
        self._run_wizard(changed_csv)
        self.assertEqual(mapping.product_id, self.product_a)
        self.assertEqual(mapping.relation_state, 'confirmed')
        self.assertEqual(mapping.reviewer_id, reviewer)
        self.assertEqual(mapping.review_date, review_date)
        self.assertEqual(mapping.woo_name, 'Título cambiado')

    def test_import_does_not_invent_matches(self):
        self._run_wizard()
        # El SKU sin producto Odoo se conserva, pero nunca se inventa pareja.
        mapping = self.Mapping.search([
            ('backend_id', '=', self.backend.id),
            ('woo_product_id', '=', 99999),
        ])
        self.assertTrue(mapping)
        self.assertFalse(mapping.product_id)
        self.assertEqual(mapping.relation_state, 'pending')

    def test_import_writes_log(self):
        self._run_wizard()
        log = self.env['amunet.woo.sync.log'].search(
            [('operation', '=', 'csv_import')], limit=1)
        self.assertTrue(log)
        self.assertEqual(log.state, 'partial')
        self.assertEqual(log.total_count, 4)
