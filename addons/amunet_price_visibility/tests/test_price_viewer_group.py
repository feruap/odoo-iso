# -*- coding: utf-8 -*-

from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


PRICE_VIEWER_LOGIN = 'fernando.ruiz@amunet.com.mx'


@tagged('post_install', '-at_install')
class TestPriceViewerGroup(TransactionCase):
    def test_only_fernando_can_view_prices(self):
        group = self.env.ref('amunet_price_visibility.group_price_viewer')
        self.env.cr.execute(
            """
            SELECT u.login
              FROM res_users u
              JOIN res_groups_users_rel rel ON rel.uid = u.id
             WHERE rel.gid = %s
               AND u.active
             ORDER BY u.login
            """,
            [group.id],
        )
        logins = [row[0] for row in self.env.cr.fetchall()]
        self.assertEqual(
            len(logins),
            1,
            'El grupo Amunet / Ver precios debe tener exactamente un usuario activo: %s' % logins,
        )
        self.assertEqual(
            logins[0],
            PRICE_VIEWER_LOGIN,
            'El unico usuario activo del grupo Amunet / Ver precios debe ser Fernando.',
        )

    def test_non_price_viewer_cannot_read_or_export_price_fields(self):
        user = self.env['res.users'].create({
            'name': 'Usuario sin precios',
            'login': 'sin.precios.test@amunet.invalid',
            'email': 'sin.precios.test@amunet.invalid',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        product = self.env['product.product'].create({
            'name': 'Producto protegido para prueba',
            'list_price': 123.0,
            'standard_price': 45.0,
        })
        product_as_user = product.with_user(user)

        with self.assertRaises(AccessError):
            product_as_user.read(['name', 'list_price'])

        with self.assertRaises(AccessError):
            product_as_user.export_data(['name', 'standard_price'])

        self.assertEqual(product_as_user.read(['name'])[0]['name'], product.name)
