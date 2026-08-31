# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSaleConfidential(TransactionCase):

    def setUp(self):
        super().setUp()
        self.confidential = self.env.ref('amunet_sale_confidential.group_sale_confidential')
        self.planner = self.env['res.users'].create({
            'name': 'Planeador sin precios',
            'login': 'test_planeador_ventas',
            'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.confidential.id,
            ])],
        })
        partner = self.env['res.partner'].create({'name': 'Cliente prueba'})
        product = self.env['product.product'].create({'name': 'Prueba rapida demo'})
        # El grupo de vendedor es "solo mis documentos": si el pedido no es del
        # planeador, la regla de registro lo bloquea antes de llegar al campo y
        # la prueba mediria lo que no es.
        self.order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'user_id': self.planner.id,
            'order_line': [(0, 0, {'product_id': product.id, 'product_uom_qty': 10})],
        })

    def test_importe_no_legible_sin_grupo_precios(self):
        order = self.order.with_user(self.planner)
        data = order.read(['name', 'amount_total'])[0]
        self.assertFalse(data.get('amount_total'),
                         'El importe no debe ser legible sin el grupo de precios')

    def test_cantidad_si_legible(self):
        line = self.order.order_line.with_user(self.planner)
        self.assertEqual(line.read(['product_uom_qty'])[0]['product_uom_qty'], 10)

    def test_exportacion_bloqueada(self):
        with self.assertRaises(AccessError):
            self.order.with_user(self.planner).export_data(['name', 'amount_total'])

    def test_grupo_precios_si_ve_importe(self):
        """Con el grupo de precios el importe sigue siendo legible."""
        viewer = self.env['res.users'].create({
            'name': 'Direccion con precios',
            'login': 'test_direccion_precios',
            'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.confidential.id,
                self.env.ref('amunet_price_visibility.group_price_viewer').id,
            ])],
        })
        self.order.user_id = viewer
        data = self.order.with_user(viewer).read(['amount_total'])[0]
        self.assertTrue(data.get('amount_total') is not False)

    def test_reporte_ventas_sin_importes(self):
        """sale.report tampoco debe soltar precios al planeador."""
        Report = self.env['sale.report'].with_user(self.planner)
        campos = Report.fields_get(allfields=['price_total', 'price_unit'])
        self.assertFalse(campos, 'sale.report no debe exponer importes sin el grupo')
