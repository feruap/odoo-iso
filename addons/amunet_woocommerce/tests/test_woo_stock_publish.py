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
        cls.piece = cls.env['product.product'].with_context(
            amunet_alta_autorizada=True).create({
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
        # En una BD con el modulo de Calidad instalado, el lote debe estar
        # LIBERADO para poder recibirse: ese es el candado del flujo. Los
        # casos que prueban el candado lo ponen en pendiente explicitamente.
        if "amunet_lot_release_state" in cls.env["stock.lot"]._fields:
            cls.lot.amunet_lot_release_state = "released"
        # Ubicacion de piezas fijada y con existencia: no se puede recibir mas
        # de lo que hay fisicamente, asi que la prueba necesita stock real.
        cls.backend.apt_pieces_location_id = cls.location_stock.id
        cls.env['stock.quant']._update_available_quantity(
            cls.piece, cls.location_stock, 1000.0, lot_id=cls.lot)
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

    def _make_reception(self, qty=40.0):
        """Recepción aceptada del lote de prueba (dispara la publicación)."""
        return self.env['amunet.woo.reception'].create({
            'backend_id': self.backend.id,
            'company_id': self.backend.company_id.id,
            'mapping_id': self.mapping.id,
            'product_id': self.piece.id,
            'lot_id': self.lot.id,
            'quantity': qty,
        })

    def test_publish_creates_ledger_and_log(self):
        """Publica una recepción aceptada: ledger + bitácora, sin HTTP real."""
        self._enable_publish()
        with mock.patch.object(
                type(self.backend), '_apt_deliver',
                return_value={'message': 'ok'}) as m_deliver:
            self._make_reception(qty=40.0)
        self.assertEqual(m_deliver.call_count, 1)
        payload = m_deliver.call_args[0][0]
        self.assertEqual(payload['product_id'], 9001)
        self.assertEqual(payload['quantity'], 40.0)
        deliveries = self.Delivery.search([
            ('backend_id', '=', self.backend.id), ('state', '=', 'published')])
        self.assertEqual(len(deliveries), 1)
        self.assertEqual(deliveries.quantity, 40.0)
        log = self.env['amunet.woo.sync.log'].search([
            ('backend_id', '=', self.backend.id),
            ('operation', '=', 'stock_publish'),
        ])
        self.assertTrue(log)
        self.assertEqual(log.done_count, 1)

    def test_publish_is_idempotent(self):
        """Reejecutar no reenvía la recepción ya publicada (idempotencia)."""
        self._enable_publish()
        with mock.patch.object(
                type(self.backend), '_apt_deliver',
                return_value={'message': 'ok'}) as m_deliver:
            self._make_reception(qty=40.0)          # auto-publica una vez
            self.backend.action_publish_stock()      # delegación -> nada nuevo
            self.backend.action_publish_stock()
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
