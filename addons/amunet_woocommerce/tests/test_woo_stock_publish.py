# -*- coding: utf-8 -*-

from unittest import mock

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import AmunetWooCommon


@tagged('post_install', '-at_install')
class TestWooStockPublish(AmunetWooCommon):
    """Camino de escritura: publicar existencias APT -> tienda.

    El HTTP hacia la tienda se simula siempre: las pruebas nunca contactan una
    tienda real. Se valida el candado, la idempotencia y la bitácora.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.piece = cls.env['product.product'].create({
            'name': 'Prueba pieza APT', 'default_code': 'APT-PZ01',
            'type': 'consu', 'is_storable': True,
        })
        cls.mapping = cls.env['amunet.woo.product.mapping'].create({
            'backend_id': cls.backend.id,
            'product_id': cls.piece.id,
            'woo_product_id': 9001,
            'woo_sku': cls.piece.default_code,
            'woo_name': cls.piece.name,
            'relation_state': 'confirmed',
        })
        cls.lot = cls.env['stock.lot'].create({
            'name': 'LOTE-APT-001',
            'product_id': cls.piece.id,
        })
        cls.Delivery = cls.env['amunet.woo.stock.delivery']

    def _fake_lot_stock(self):
        """Datos sintéticos de un lote liberado, sin depender de calidad."""
        return [{
            'lot': self.lot,
            'lot_number': self.lot.name,
            'quantity': 40.0,
            'expiration_month': 12,
            'expiration_year': 2027,
        }]

    def _enable_publish(self):
        self.backend.write({
            'allow_stock_publish': True,
            'apt_wp_user': 'apt-bot',
            'apt_wp_app_password': 'xxxx xxxx xxxx',
        })

    # ------------------------------------------------------------------

    def test_publish_disabled_raises(self):
        """Sin el candado, publicar está prohibido."""
        self.assertFalse(self.backend.allow_stock_publish)
        with self.assertRaises(UserError):
            self.backend.action_publish_stock()

    def test_deliver_requires_credentials(self):
        """Con candado pero sin Application Password, el POST se bloquea."""
        self.backend.write({'allow_stock_publish': True})
        with self.assertRaises(UserError):
            self.backend._apt_deliver({'product_id': 1, 'quantity': 1})

    def test_publish_creates_ledger_and_log(self):
        """Publica un lote liberado: ledger + bitácora, sin HTTP real."""
        self._enable_publish()
        with mock.patch.object(
                type(self.backend), '_read_released_piece_stock',
                return_value=self._fake_lot_stock()), \
             mock.patch.object(
                type(self.backend), '_apt_deliver',
                return_value={'message': 'ok'}) as m_deliver:
            self.backend.action_publish_stock()
        self.assertEqual(m_deliver.call_count, 1)
        payload = m_deliver.call_args[0][0]
        self.assertEqual(payload['product_id'], 9001)
        self.assertEqual(payload['expiration_month'], 12)
        self.assertEqual(payload['expiration_year'], 2027)
        deliveries = self.Delivery.search([('backend_id', '=', self.backend.id)])
        self.assertEqual(len(deliveries), 1)
        self.assertEqual(deliveries.state, 'published')
        self.assertEqual(deliveries.quantity, 40.0)
        log = self.env['amunet.woo.sync.log'].search([
            ('backend_id', '=', self.backend.id),
            ('operation', '=', 'stock_publish'),
        ])
        self.assertTrue(log)
        self.assertEqual(log.done_count, 1)

    def test_publish_is_idempotent(self):
        """Reejecutar no reenvía el lote ya publicado (idempotencia)."""
        self._enable_publish()
        with mock.patch.object(
                type(self.backend), '_read_released_piece_stock',
                return_value=self._fake_lot_stock()), \
             mock.patch.object(
                type(self.backend), '_apt_deliver',
                return_value={'message': 'ok'}) as m_deliver:
            self.backend.action_publish_stock()
            self.backend.action_publish_stock()
        # El segundo llamado no vuelve a hacer POST del mismo lote.
        self.assertEqual(m_deliver.call_count, 1)
        deliveries = self.Delivery.search([
            ('backend_id', '=', self.backend.id),
            ('state', '=', 'published'),
        ])
        self.assertEqual(len(deliveries), 1)

    def test_read_side_returns_list(self):
        """La lectura de stock por lote liberado no truena si falta calidad."""
        # Sin el módulo de calidad, el campo puede no existir: debe devolver [].
        result = self.backend._read_released_piece_stock(self.mapping)
        self.assertIsInstance(result, list)
