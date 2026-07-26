# -*- coding: utf-8 -*-

import base64

from odoo import fields

from .common import AmunetWooCommon


class TestWooMultiCompany(AmunetWooCommon):

    def setUp(self):
        super().setUp()
        self.other_company = self.env['res.company'].create({
            'name': 'Otra compañía Woo',
        })
        self.env.user.company_ids |= self.other_company
        self.foreign_product = self.env['product.product'].with_company(
            self.other_company).create({
                'name': 'Producto de otra compañía',
                'default_code': 'SOLOOTRA01',
                'type': 'consu',
                'is_storable': True,
                'company_id': self.other_company.id,
            })

    def test_catalog_get_does_not_link_product_from_other_company(self):
        result = self.Mapping._upsert_from_woo(self.backend, {
            'id': 880001,
            'sku': 'SOLOOTRA01',
            'name': 'Artículo Woo multiempresa',
            'type': 'simple',
            'status': 'publish',
            'images': [],
        })
        self.assertEqual(result, 'unmatched_created')
        mapping = self.Mapping.search([
            ('backend_id', '=', self.backend.id),
            ('woo_product_id', '=', 880001),
        ])
        self.assertTrue(mapping)
        self.assertFalse(mapping.product_id)

    def test_csv_does_not_link_product_from_other_company(self):
        content = (
            'woo_id,woo_sku,titulo,piezas,odoo_default_code,odoo_track,'
            'odoo_use_exp,confianza,metodo,justificacion\n'
            '880002,SOLOOTRA01,Artículo Woo multiempresa,1,SOLOOTRA01,,,'
            'alta,sku,\n'
        )
        wizard = self.env['amunet.woo.mapping.import.wizard'].create({
            'backend_id': self.backend.id,
            'data_file': base64.b64encode(content.encode('utf-8')),
            'filename': 'multiempresa.csv',
            'snapshot_date': fields.Datetime.to_datetime(
                '2026-07-24 07:30:01'),
        })
        wizard.action_import()
        mapping = self.Mapping.search([
            ('backend_id', '=', self.backend.id),
            ('woo_product_id', '=', 880002),
        ])
        self.assertTrue(mapping)
        self.assertFalse(mapping.product_id)
        self.assertEqual(wizard.not_found_count, 1)
