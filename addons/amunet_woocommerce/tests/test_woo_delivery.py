# -*- coding: utf-8 -*-

from unittest import mock

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import AmunetWooCommon


@tagged('post_install', '-at_install')
class TestWooDelivery(AmunetWooCommon):
    """Entrega de Acondicionado -> recepción del almacén de venta.

    Valida el control de dos partes: quien entrega declara (completa/parcial),
    quien recibe cuenta y confirma, y una diferencia RECHAZA la entrega
    completa. Valida además el candado regulatorio: recibir material sin
    liberación SÍ se permite, pero queda RETENIDO y no se publica hasta que
    Calidad libere o se autorice bajo concesión. El HTTP a la tienda se simula
    siempre; las pruebas nunca contactan una tienda real.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.piece = cls.env['product.product'].with_context(
            amunet_alta_autorizada=True).create({
            'name': 'Pieza entrega APT', 'default_code': 'APT-ENT01',
            'type': 'consu', 'is_storable': True,
        })
        cls.mapping = cls.env['amunet.woo.product.mapping'].create({
            'backend_id': cls.backend.id,
            'product_id': cls.piece.id,
            'woo_product_id': 8888,
            'woo_sku': cls.piece.default_code,
            'woo_name': cls.piece.name,
            'relation_state': 'confirmed',
        })
        # La ubicacion de piezas se fija explicitamente para que la prueba no
        # dependa de que exista "APT/Existencias_Presentacion 1 pieza".
        cls.backend.apt_pieces_location_id = cls.location_stock.id
        cls.Delivery = cls.env['amunet.woo.delivery']
        cls.Reception = cls.env['amunet.woo.reception']
        cls.StockDelivery = cls.env['amunet.woo.stock.delivery']
        cls.tiene_calidad = (
            'amunet_lot_release_state' in cls.env['stock.lot']._fields)
        # Grupos usados por el flujo.
        cls.env.user.group_ids |= cls.env.ref(
            'amunet_woocommerce.group_woo_acondicionado')

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def _make_lot(self, name, released=True):
        lot = self.env['stock.lot'].create({
            'name': name, 'product_id': self.piece.id,
        })
        if self.tiene_calidad and released:
            lot.amunet_lot_release_state = 'released'
        return lot

    def _make_production(self, lot_name, qty=100.0):
        """Orden de fabricación cuyo NOMBRE es el del lote (convención Amunet)."""
        mo = self.env['mrp.production'].create({
            'product_id': self.piece.id,
            'product_qty': qty,
            'picking_type_id': self.manu_type.id,
        })
        mo.name = lot_name
        return mo

    def _stock(self, lot, qty):
        self.env['stock.quant']._update_available_quantity(
            self.piece, self.location_stock, qty, lot_id=lot)

    def _enable_publish(self):
        self.backend.write({
            'allow_stock_publish': True,
            'apt_wp_user': 'apt-bot',
            'apt_wp_app_password': 'xxxx xxxx xxxx',
        })

    def _autorizador(self):
        self.env.user.group_ids |= self.env.ref(
            'amunet_woocommerce.group_woo_autoriza_concesion')

    # ------------------------------------------------------------------
    # Entrega completa / parcial
    # ------------------------------------------------------------------

    def test_entrega_completa_toma_todo_lo_pendiente(self):
        lot = self._make_lot('ENT-COMPLETA')
        self._stock(lot, 60.0)
        mo = self._make_production('ENT-COMPLETA')
        d = self.Delivery._crear_desde_produccion(mo, 'completa')
        self.assertEqual(d.tipo, 'completa')
        self.assertEqual(d.quantity_delivered, 60.0)
        self.assertEqual(d.lot_id, lot)
        self.assertEqual(d.product_id, self.piece)
        self.assertEqual(d.state, 'por_recibir')
        self.assertEqual(d.delivered_by, self.env.user)

    def test_entrega_parcial_respeta_la_cantidad(self):
        lot = self._make_lot('ENT-PARCIAL')
        self._stock(lot, 100.0)
        mo = self._make_production('ENT-PARCIAL')
        d = self.Delivery._crear_desde_produccion(mo, 'parcial', quantity=25.0)
        self.assertEqual(d.quantity_delivered, 25.0)
        # Queda pendiente el resto para una segunda entrega.
        self.assertEqual(self.Delivery._pending_qty_for_lot(lot), 75.0)

    def test_no_se_puede_entregar_mas_de_lo_pendiente(self):
        lot = self._make_lot('ENT-EXCESO')
        self._stock(lot, 30.0)
        mo = self._make_production('ENT-EXCESO')
        with self.assertRaises(UserError):
            self.Delivery._crear_desde_produccion(mo, 'parcial', quantity=31.0)
        # Dos parciales que en total se pasan: la segunda debe fallar.
        self.Delivery._crear_desde_produccion(mo, 'parcial', quantity=20.0)
        with self.assertRaises(UserError):
            self.Delivery._crear_desde_produccion(mo, 'parcial', quantity=15.0)

    def test_cantidad_entregada_debe_ser_positiva(self):
        lot = self._make_lot('ENT-CERO')
        self._stock(lot, 10.0)
        mo = self._make_production('ENT-CERO')
        with self.assertRaises(ValidationError):
            self.Delivery.create({
                'production_id': mo.id, 'lot_id': lot.id,
                'product_id': self.piece.id,
                'tipo': 'parcial', 'quantity_delivered': 0.0,
            })

    # ------------------------------------------------------------------
    # Recepción: coincide / no coincide
    # ------------------------------------------------------------------

    def test_recepcion_que_coincide_genera_recepcion(self):
        lot = self._make_lot('ENT-OK')
        self._stock(lot, 40.0)
        mo = self._make_production('ENT-OK')
        d = self.Delivery._crear_desde_produccion(mo, 'completa')
        d.quantity_received = 40.0
        d.action_recibir()
        self.assertEqual(d.state, 'recibida')
        self.assertEqual(d.received_by, self.env.user)
        self.assertTrue(d.reception_id)
        self.assertEqual(d.reception_id.quantity, 40.0)
        self.assertEqual(d.reception_id.lot_id, lot)
        self.assertEqual(d.reception_id.delivery_id, d)

    def test_diferencia_rechaza_la_entrega_completa(self):
        """Regla de Luis: si no coincide, se rechaza COMPLETA para aclarar."""
        lot = self._make_lot('ENT-DIF')
        self._stock(lot, 50.0)
        mo = self._make_production('ENT-DIF')
        d = self.Delivery._crear_desde_produccion(mo, 'completa')
        self.assertEqual(d.quantity_delivered, 50.0)
        d.quantity_received = 45.0
        d.action_recibir()
        self.assertEqual(d.state, 'rechazada')
        self.assertFalse(d.reception_id)
        self.assertIn('45', d.rejection_reason)
        # Al rechazarse, el material vuelve a quedar pendiente por entregar.
        self.assertEqual(self.Delivery._pending_qty_for_lot(lot), 50.0)

    def test_no_se_recibe_sin_capturar_cantidad(self):
        lot = self._make_lot('ENT-SINCANT')
        self._stock(lot, 20.0)
        mo = self._make_production('ENT-SINCANT')
        d = self.Delivery._crear_desde_produccion(mo, 'completa')
        with self.assertRaises(UserError):
            d.action_recibir()

    # ------------------------------------------------------------------
    # Liberación de Calidad, retención y concesión
    # ------------------------------------------------------------------

    def test_sin_liberacion_se_entrega_y_recibe_pero_no_es_vendible(self):
        if not self.tiene_calidad:
            self.skipTest('Módulo de Calidad no instalado en esta BD de prueba')
        lot = self._make_lot('ENT-RETENIDO', released=False)
        self._stock(lot, 30.0)
        mo = self._make_production('ENT-RETENIDO')
        self._enable_publish()
        with mock.patch.object(type(self.backend), '_apt_deliver',
                               return_value={'message': 'ok'}) as m:
            d = self.Delivery._crear_desde_produccion(mo, 'completa')
            self.assertTrue(d.sin_liberacion)
            self.assertFalse(d.vendible)
            d.quantity_received = 30.0
            d.action_recibir()
        # Se recibió físicamente...
        self.assertEqual(d.state, 'recibida')
        self.assertTrue(d.reception_id)
        # ...pero NO se publicó: material retenido.
        self.assertEqual(m.call_count, 0)
        self.assertFalse(d.reception_id.vendible)
        self.assertEqual(d.reception_id.state, 'aceptada')

    def test_autorizacion_lo_vuelve_vendible_y_registra_al_autorizante(self):
        if not self.tiene_calidad:
            self.skipTest('Módulo de Calidad no instalado en esta BD de prueba')
        lot = self._make_lot('ENT-CONCESION', released=False)
        self._stock(lot, 12.0)
        mo = self._make_production('ENT-CONCESION')
        self._enable_publish()
        self._autorizador()
        with mock.patch.object(type(self.backend), '_apt_deliver',
                               return_value={'message': 'ok'}) as m:
            d = self.Delivery._crear_desde_produccion(mo, 'completa')
            d.quantity_received = 12.0
            d.action_recibir()
            self.assertEqual(m.call_count, 0)   # retenido todavía
            d.authorization_note = 'Urgente para pedido del cliente'
            d.action_autorizar()
        self.assertEqual(d.authorized_by, self.env.user)
        self.assertTrue(d.authorized_date)
        self.assertTrue(d.vendible)
        self.assertTrue(d.reception_id.vendible)
        # Al autorizar, el material sí se publica.
        self.assertEqual(m.call_count, 1)
        self.assertEqual(d.reception_id.state, 'publicada')

    def test_autorizar_sin_facultad_se_rechaza(self):
        if not self.tiene_calidad:
            self.skipTest('Módulo de Calidad no instalado en esta BD de prueba')
        lot = self._make_lot('ENT-NOFACULTAD', released=False)
        self._stock(lot, 8.0)
        mo = self._make_production('ENT-NOFACULTAD')
        d = self.Delivery._crear_desde_produccion(mo, 'completa')
        sin_facultad = self.env['res.users'].create({
            'name': 'Operador sin facultad',
            'login': 'woo_sin_facultad_test',
            'group_ids': [(6, 0, [
                self.env.ref('amunet_woocommerce.group_woo_revisor').id,
                self.env.ref('amunet_woocommerce.group_woo_acondicionado').id,
            ])],
        })
        with self.assertRaises(UserError):
            d.with_user(sin_facultad).action_autorizar()
        self.assertFalse(d.authorized_by)

    def test_no_se_autoriza_un_lote_ya_liberado(self):
        if not self.tiene_calidad:
            self.skipTest('Módulo de Calidad no instalado en esta BD de prueba')
        lot = self._make_lot('ENT-YALIBERADO')
        self._stock(lot, 5.0)
        mo = self._make_production('ENT-YALIBERADO')
        d = self.Delivery._crear_desde_produccion(mo, 'completa')
        self._autorizador()
        self.assertTrue(d.vendible)
        with self.assertRaises(UserError):
            d.action_autorizar()

    # ------------------------------------------------------------------
    # Regresión: el error de 795 pz sobre un lote de 265
    # ------------------------------------------------------------------

    def test_regresion_no_se_puede_sobre_recibir_un_lote(self):
        """Antes, cada clic recibía TODA la existencia: 3 clics = 795 de 265."""
        lot = self._make_lot('ENT-265')
        self._stock(lot, 265.0)
        # Primera recepción directa: toma las 265 pendientes.
        lot.action_aceptar_recepcion_venta()
        recibido = sum(self.Reception.search([
            ('lot_id', '=', lot.id), ('state', '!=', 'cancelada'),
        ]).mapped('quantity'))
        self.assertEqual(recibido, 265.0)
        # Segunda: ya no queda nada pendiente, debe negarse.
        with self.assertRaises(UserError):
            lot.action_aceptar_recepcion_venta()
        # Y una recepción manual que se pase tampoco entra.
        with self.assertRaises(ValidationError):
            self.Reception.create({
                'backend_id': self.backend.id,
                'company_id': self.backend.company_id.id,
                'product_id': self.piece.id,
                'lot_id': lot.id,
                'quantity': 1.0,
            })
        total = sum(self.Reception.search([
            ('lot_id', '=', lot.id), ('state', '!=', 'cancelada'),
        ]).mapped('quantity'))
        self.assertEqual(total, 265.0, 'No se puede recibir mas que el fisico')

    def test_recepcion_directa_descuenta_lo_ya_recibido(self):
        lot = self._make_lot('ENT-DESCUENTA')
        self._stock(lot, 100.0)
        self.Reception.create({
            'backend_id': self.backend.id,
            'company_id': self.backend.company_id.id,
            'product_id': self.piece.id,
            'lot_id': lot.id,
            'quantity': 30.0,
        })
        lot.action_aceptar_recepcion_venta()
        total = sum(self.Reception.search([
            ('lot_id', '=', lot.id), ('state', '!=', 'cancelada'),
        ]).mapped('quantity'))
        self.assertEqual(total, 100.0, 'Debe recibir solo las 70 que faltaban')

    # ------------------------------------------------------------------
    # Cancelación
    # ------------------------------------------------------------------

    def test_no_se_cancela_una_entrega_ya_recibida(self):
        lot = self._make_lot('ENT-CANCEL')
        self._stock(lot, 15.0)
        mo = self._make_production('ENT-CANCEL')
        d = self.Delivery._crear_desde_produccion(mo, 'completa')
        d.quantity_received = 15.0
        d.action_recibir()
        with self.assertRaises(UserError):
            d.action_cancelar()

    # ------------------------------------------------------------------
    # Regularización de material histórico (sin entrega de origen)
    # ------------------------------------------------------------------

    def _recepcion_historica(self, lot_name, qty):
        """Recepción como las que ya existían antes de este flujo: sin entrega.

        Es el caso real de las 66 pz del lote 0826/01/PSS que llegaron al
        almacén con el lote todavía 'pendiente' de Calidad.
        """
        lot = self._make_lot(lot_name, released=False)
        self._stock(lot, qty)
        return self.Reception.create({
            'backend_id': self.backend.id,
            'company_id': self.backend.company_id.id,
            'product_id': self.piece.id,
            'lot_id': lot.id,
            'quantity': qty,
        })

    def test_historico_sin_entrega_queda_retenido(self):
        if not self.tiene_calidad:
            self.skipTest('Módulo de Calidad no instalado en esta BD de prueba')
        rec = self._recepcion_historica('HIST-RETENIDO', 66.0)
        self.assertFalse(rec.delivery_id)
        self.assertTrue(rec.sin_liberacion)
        self.assertFalse(rec.vendible)
        self.assertTrue(rec.requiere_regularizacion)

    def test_regularizar_recepcion_historica_la_vuelve_vendible(self):
        if not self.tiene_calidad:
            self.skipTest('Módulo de Calidad no instalado en esta BD de prueba')
        rec = self._recepcion_historica('HIST-REGULARIZA', 66.0)
        self._enable_publish()
        self._autorizador()
        rec.authorization_note = 'Regularización de material histórico'
        with mock.patch.object(type(self.backend), '_apt_deliver',
                               return_value={'message': 'ok'}) as m:
            rec.action_autorizar()
        self.assertEqual(rec.authorized_by, self.env.user)
        self.assertTrue(rec.authorized_date)
        self.assertTrue(rec.vendible)
        self.assertFalse(rec.requiere_regularizacion)
        # Al regularizarse, lo retenido sí se publica.
        self.assertEqual(m.call_count, 1)
        self.assertEqual(rec.state, 'publicada')

    def test_regularizar_sin_facultad_se_rechaza(self):
        if not self.tiene_calidad:
            self.skipTest('Módulo de Calidad no instalado en esta BD de prueba')
        rec = self._recepcion_historica('HIST-NOFACULTAD', 10.0)
        sin_facultad = self.env['res.users'].create({
            'name': 'Almacen sin facultad',
            'login': 'woo_regulariza_sin_facultad_test',
            'group_ids': [(6, 0, [
                self.env.ref('amunet_woocommerce.group_woo_revisor').id,
            ])],
        })
        with self.assertRaises(UserError):
            rec.with_user(sin_facultad).action_autorizar()
        self.assertFalse(rec.authorized_by)
        self.assertFalse(rec.vendible)

    def test_regularizacion_en_lote_desde_la_lista(self):
        """Se pueden regularizar VARIAS recepciones de una sola vez."""
        if not self.tiene_calidad:
            self.skipTest('Módulo de Calidad no instalado en esta BD de prueba')
        r1 = self._recepcion_historica('HIST-BULK-1', 20.0)
        r2 = self._recepcion_historica('HIST-BULK-2', 30.0)
        r3 = self._recepcion_historica('HIST-BULK-3', 40.0)
        seleccion = r1 | r2 | r3
        self.assertFalse(any(seleccion.mapped('vendible')))
        self._autorizador()
        seleccion.action_autorizar()
        self.assertTrue(all(seleccion.mapped('vendible')))
        for rec in seleccion:
            self.assertEqual(rec.authorized_by, self.env.user)
        self.assertFalse(any(seleccion.mapped('requiere_regularizacion')))

    def test_no_se_regulariza_dos_veces(self):
        if not self.tiene_calidad:
            self.skipTest('Módulo de Calidad no instalado en esta BD de prueba')
        rec = self._recepcion_historica('HIST-DOBLE', 5.0)
        self._autorizador()
        rec.action_autorizar()
        with self.assertRaises(UserError):
            rec.action_autorizar()
