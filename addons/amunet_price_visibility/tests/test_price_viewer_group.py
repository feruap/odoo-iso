# -*- coding: utf-8 -*-

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
