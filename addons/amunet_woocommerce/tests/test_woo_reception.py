# -*- coding: utf-8 -*-

from unittest import mock

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import AmunetWooCommon


@tagged('post_install', '-at_install')
class TestWooReception(AmunetWooCommon):
    """Recepción de material para venta (woolibre).

    Valida: aceptación auditable, candado de cantidad, candado de liberación
    (si Calidad está instalado), y la publicación RECEPCIÓN-céntrica con
    idempotencia por recepción y soporte a entregas parciales. El HTTP a la
    tienda se simula siempre; las pruebas nunca contactan una tienda real.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.piece = cls.env['product.product'].with_context(
            amunet_alta_autorizada=True).create({
            'name': 'Pieza recepción APT', 'default_code': 'APT-REC01',
            'type': 'consu', 'is_storable': True,
        })
        cls.mapping = cls.env['amunet.woo.product.mapping'].create({
            'backend_id': cls.backend.id,
            'product_id': cls.piece.id,
            'woo_product_id': 7777,
            'woo_sku': cls.piece.default_code,
            'woo_name': cls.piece.name,
            'relation_state': 'confirmed',
        })
        cls.lot = cls.env['stock.lot'].create({
            'name': 'LOTE-REC-001', 'product_id': cls.piece.id,
        })
        # El lote debe estar LIBERADO por Calidad para que lo recibido sea
        # VENDIBLE y se publique. Recibir sin liberar tambien se permite, pero
        # entonces queda retenido (eso se prueba aparte).
        if "amunet_lot_release_state" in cls.env["stock.lot"]._fields:
            cls.lot.amunet_lot_release_state = "released"
        # Ubicacion de piezas fijada y con existencia: no se puede recibir mas
        # de lo que hay fisicamente, asi que las pruebas necesitan stock real.
        cls.backend.apt_pieces_location_id = cls.location_stock.id
        cls.env['stock.quant']._update_available_quantity(
            cls.piece, cls.location_stock, 1000.0, lot_id=cls.lot)
        cls.Reception = cls.env['amunet.woo.reception']
        cls.Delivery = cls.env['amunet.woo.stock.delivery']

    def _enable_publish(self):
        self.backend.write({
            'allow_stock_publish': True,
            'apt_wp_user': 'apt-bot',
            'apt_wp_app_password': 'xxxx xxxx xxxx',
        })

    def _make_reception(self, qty=10.0, lot=None):
        return self.Reception.create({
            'backend_id': self.backend.id,
            'company_id': self.backend.company_id.id,
            'mapping_id': self.mapping.id,
            'product_id': self.piece.id,
            'lot_id': (lot or self.lot).id,
            'quantity': qty,
        })

    # ------------------------------------------------------------------
    # Aceptación y candados
    # ------------------------------------------------------------------

    def test_accept_records_user_qty_and_lot(self):
        rec = self._make_reception(qty=15.0)
        self.assertEqual(rec.state, 'aceptada')
        self.assertEqual(rec.quantity, 15.0)
        self.assertEqual(rec.received_by, self.env.user)
        self.assertTrue(rec.received_date)
        self.assertEqual(rec.lot_number, 'LOTE-REC-001')
        self.assertEqual(rec.product_id, self.piece)

    def test_quantity_must_be_positive(self):
        with self.assertRaises(ValidationError):
            self._make_reception(qty=0.0)
        with self.assertRaises(ValidationError):
            self._make_reception(qty=-3.0)

    def test_release_gate_soft_dependency(self):
        """Sin el módulo de Calidad no hay concepto de liberación."""
        Lot = self.env['stock.lot']
        if 'amunet_lot_release_state' in Lot._fields:
            self.skipTest(
                'Con Calidad instalado el candado se prueba en '
                'test_sin_liberacion_se_recibe_pero_queda_retenido')
        self.assertFalse(self.Reception._release_gate_field_exists())
        rec = self._make_reception(qty=5.0)
        self.assertEqual(rec.state, 'aceptada')
        self.assertTrue(rec.vendible)

    def test_sin_liberacion_se_recibe_pero_queda_retenido(self):
        """Recibir sin liberación SÍ se permite; lo que se bloquea es vender.

        Cambio de diseño pedido por almacén: a veces el material urge y se
        entrega antes de que Calidad libere. Entonces entra RETENIDO.
        """
        Lot = self.env['stock.lot']
        if 'amunet_lot_release_state' not in Lot._fields:
            self.skipTest('Módulo de Calidad no instalado en esta BD de prueba')
        # Lote NUEVO, nunca liberado: Calidad bloquea modificar campos
        # criticos de un lote ya liberado, asi que no se puede "des-liberar".
        pendiente = Lot.create({
            'name': 'LOTE-REC-PEND', 'product_id': self.piece.id,
        })
        self.env['stock.quant']._update_available_quantity(
            self.piece, self.location_stock, 50.0, lot_id=pendiente)
        self.assertEqual(pendiente.amunet_lot_release_state, 'pending')
        self._enable_publish()
        with mock.patch.object(type(self.backend), '_apt_deliver',
                               return_value={'message': 'ok'}) as m:
            rec = self._make_reception(qty=5.0, lot=pendiente)
        # Se recibe...
        self.assertEqual(rec.state, 'aceptada')
        self.assertTrue(rec.sin_liberacion)
        # ...pero NO es vendible ni se publica.
        self.assertFalse(rec.vendible)
        self.assertEqual(m.call_count, 0)

    # ------------------------------------------------------------------
    # Publicación RECEPCIÓN-céntrica
    # ------------------------------------------------------------------

    def test_accept_without_publish_flag_does_not_deliver(self):
        """Aceptar la recepción NO requiere el candado de la tienda; sin él,
        simplemente no publica (no llama al endpoint)."""
        with mock.patch.object(type(self.backend), '_apt_deliver') as m:
            rec = self._make_reception(qty=8.0)
        self.assertEqual(rec.state, 'aceptada')
        self.assertEqual(m.call_count, 0)

    def test_accept_autopublishes_when_enabled(self):
        self._enable_publish()
        with mock.patch.object(type(self.backend), '_apt_deliver',
                               return_value={'message': 'ok'}) as m:
            rec = self._make_reception(qty=12.0)
        self.assertEqual(m.call_count, 1)
        payload = m.call_args[0][0]
        self.assertEqual(payload['product_id'], 7777)
        self.assertEqual(payload['quantity'], 12.0)
        self.assertEqual(payload['lot_number'], 'LOTE-REC-001')
        self.assertEqual(rec.state, 'publicada')
        deliveries = self.Delivery.search([
            ('backend_id', '=', self.backend.id), ('state', '=', 'published')])
        self.assertEqual(len(deliveries), 1)
        self.assertEqual(deliveries.quantity, 12.0)
        log = self.env['amunet.woo.sync.log'].search([
            ('backend_id', '=', self.backend.id),
            ('operation', '=', 'stock_publish')])
        self.assertTrue(log)

    def test_manual_publish_action(self):
        """Se acepta con publicación apagada; al habilitarla y publicar manual,
        sale una sola vez."""
        rec = self._make_reception(qty=9.0)
        self.assertEqual(rec.state, 'aceptada')
        self._enable_publish()
        with mock.patch.object(type(self.backend), '_apt_deliver',
                               return_value={'message': 'ok'}) as m:
            self.backend.action_publicar_recepciones()
        self.assertEqual(m.call_count, 1)
        self.assertEqual(rec.state, 'publicada')

    def test_partial_receptions_each_publish_once(self):
        """Entregas parciales del MISMO lote: cada recepción se publica una vez."""
        self._enable_publish()
        with mock.patch.object(type(self.backend), '_apt_deliver',
                               return_value={'message': 'ok'}) as m:
            r1 = self._make_reception(qty=2.0)
            r2 = self._make_reception(qty=5.0)
        self.assertEqual(m.call_count, 2)
        self.assertEqual(r1.state, 'publicada')
        self.assertEqual(r2.state, 'publicada')
        deliveries = self.Delivery.search([
            ('backend_id', '=', self.backend.id), ('state', '=', 'published')])
        self.assertEqual(len(deliveries), 2)
        self.assertEqual(sum(deliveries.mapped('quantity')), 7.0)

    def test_publish_is_idempotent(self):
        """Reejecutar la publicación no reenvía una recepción ya publicada."""
        self._enable_publish()
        with mock.patch.object(type(self.backend), '_apt_deliver',
                               return_value={'message': 'ok'}) as m:
            self._make_reception(qty=4.0)   # auto-publica una vez
            self.backend.action_publicar_recepciones()
            self.backend.action_publicar_recepciones()
        self.assertEqual(m.call_count, 1)
        deliveries = self.Delivery.search([
            ('backend_id', '=', self.backend.id), ('state', '=', 'published')])
        self.assertEqual(len(deliveries), 1)

    def test_legacy_publish_stock_delegates_to_receptions(self):
        """La acción legada action_publish_stock ahora publica recepciones."""
        rec = self._make_reception(qty=6.0)
        self._enable_publish()
        with mock.patch.object(type(self.backend), '_apt_deliver',
                               return_value={'message': 'ok'}) as m:
            self.backend.action_publish_stock()
        self.assertEqual(m.call_count, 1)
        self.assertEqual(rec.state, 'publicada')
