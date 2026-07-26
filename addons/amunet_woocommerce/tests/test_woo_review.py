# -*- coding: utf-8 -*-

from odoo.exceptions import AccessError

from .common import AmunetWooCommon


class TestWooReview(AmunetWooCommon):

    def setUp(self):
        super().setUp()
        self.product = self._make_product('Kit revisión', 'REVISA01')
        self.mapping = self._make_mapping(self.product, 700001)
        group_revisor = self.env.ref('amunet_woocommerce.group_woo_revisor')
        group_consulta = self.env.ref('amunet_woocommerce.group_woo_consulta')
        self.revisor = self.env['res.users'].create({
            'name': 'Revisor Woo',
            'login': 'woo_revisor_test',
            'group_ids': [(6, 0, [group_revisor.id])],
        })
        self.consulta = self.env['res.users'].create({
            'name': 'Consulta Woo',
            'login': 'woo_consulta_test',
            'group_ids': [(6, 0, [group_consulta.id])],
        })

    def test_review_is_auditable(self):
        self.mapping.action_confirm()
        self.assertEqual(self.mapping.relation_state, 'confirmed')
        self.assertEqual(self.mapping.reviewer_id, self.env.user)
        self.assertTrue(self.mapping.review_date)
        # El módulo deja un mensaje explícito además de revisor y fecha.
        audit_messages = self.mapping.message_ids.filtered(
            lambda msg: 'Revisión del vínculo actualizada' in (msg.body or ''))
        self.assertTrue(audit_messages)
        self.mapping.action_reject()
        self.assertEqual(self.mapping.relation_state, 'rejected')
        self.mapping.action_reset_pending()
        self.assertEqual(self.mapping.relation_state, 'pending')

    def test_revisor_can_edit_relation_fields(self):
        mapping = self.mapping.with_user(self.revisor)
        mapping.write({
            'relation_state': 'confirmed',
            'confidence': 'medium',
            'review_notes': 'Revisado contra catálogo.',
            'supply_classification': 'purchased_qc',
        })
        self.assertEqual(self.mapping.relation_state, 'confirmed')
        self.assertEqual(self.mapping.confidence, 'medium')

    def test_revisor_cannot_edit_woo_or_config_fields(self):
        mapping = self.mapping.with_user(self.revisor)
        with self.assertRaises(AccessError):
            mapping.write({'woo_sku': 'HACKEADO'})

    def test_revisor_can_change_product_and_stamp_review(self):
        other = self._make_product('Otro', 'OTRO01')
        mapping = self.mapping.with_user(self.revisor)
        mapping.write({'product_id': other.id})
        self.assertEqual(self.mapping.product_id, other)
        self.assertEqual(self.mapping.relation_state, 'pending')
        self.assertEqual(self.mapping.reviewer_id, self.revisor)
        self.assertTrue(self.mapping.review_date)

    def test_catalog_get_preserves_rejected_unmatched_review(self):
        mapping = self.Mapping.create({
            'backend_id': self.backend.id,
            'woo_product_id': 700002,
            'woo_sku': self.product.default_code,
            'woo_name': 'Pendiente original',
        })
        mapping.action_reject()
        reviewer = mapping.reviewer_id
        review_date = mapping.review_date
        result = self.Mapping._upsert_from_woo(self.backend, {
            'id': 700002,
            'sku': self.product.default_code,
            'name': 'Nombre actualizado desde Woo',
            'type': 'simple',
            'status': 'publish',
            'images': [],
        })
        self.assertEqual(result, 'unmatched_updated')
        self.assertFalse(mapping.product_id)
        self.assertEqual(mapping.relation_state, 'rejected')
        self.assertEqual(mapping.reviewer_id, reviewer)
        self.assertEqual(mapping.review_date, review_date)
        self.assertEqual(mapping.woo_name, 'Nombre actualizado desde Woo')

    def test_consulta_is_read_only(self):
        mapping = self.mapping.with_user(self.consulta)
        self.assertTrue(mapping.woo_sku)  # puede leer
        with self.assertRaises(AccessError):
            mapping.write({'relation_state': 'confirmed'})

    def test_consulta_cannot_touch_config_models(self):
        backend = self.env['amunet.woo.backend'].create({
            'name': 'Tienda test',
            'store_url': 'https://tst.example.com',
        })
        with self.assertRaises(AccessError):
            backend.with_user(self.consulta).write({'name': 'Otro nombre'})
        profile = self.env['amunet.woo.long.process'].create({
            'name': 'Perfil test',
            'product_id': self.product.id,
            'master_product_id': self._make_product('HM', 'HMREV01').id,
        })
        with self.assertRaises(AccessError):
            profile.with_user(self.revisor).write({'scrap_percent': 10.0})
