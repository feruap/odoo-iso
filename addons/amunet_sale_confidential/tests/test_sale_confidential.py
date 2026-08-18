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
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.confidential.id,
            ])],
        })
        partner = self.env['res.partner'].create({'name': 'Cliente prueba'})
        product = self.env['product.product'].create({'name': 'Prueba rapida demo'})
        self.order = self.env['sale.order'].create({
            'partner_id': partner.id,
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
