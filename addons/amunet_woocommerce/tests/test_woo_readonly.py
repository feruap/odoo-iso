# -*- coding: utf-8 -*-

from pathlib import Path

from odoo.modules import get_module_path

from .common import AmunetWooCommon

# Patrones prohibidos: cualquier escritura HTTP hacia WooCommerce o cron.
FORBIDDEN_PY = (
    'requests.post', 'requests.put', 'requests.patch', 'requests.delete',
    "'POST'", '"POST"', "'PUT'", '"PUT"', "'PATCH'", '"PATCH"',
    "'DELETE'", '"DELETE"', '_cron_',
)


class TestWooReadOnly(AmunetWooCommon):

    def test_invalid_total_pages_header_is_bounded(self):
        class Response:
            headers = {'X-WP-TotalPages': 'no-numérico'}

        self.assertEqual(self.backend._bounded_total_pages(Response()), 1)

    def test_no_write_http_methods_in_source(self):
        module_path = Path(get_module_path('amunet_woocommerce'))
        offenders = []
        for py_file in module_path.rglob('*.py'):
            if 'tests' in py_file.parts:
                continue
            content = py_file.read_text(encoding='utf-8')
            for pattern in FORBIDDEN_PY:
                if pattern in content:
                    offenders.append('%s: %s' % (py_file.name, pattern))
        self.assertFalse(
            offenders,
            'Se encontraron métodos de escritura HTTP o cron: %s' % offenders)

    def test_no_cron_in_module_data(self):
        module_path = Path(get_module_path('amunet_woocommerce'))
        for xml_file in module_path.rglob('*.xml'):
            content = xml_file.read_text(encoding='utf-8')
            self.assertNotIn(
                'ir.cron', content,
                'El módulo no debe definir cron (%s)' % xml_file.name)
        cron_count = self.env['ir.cron'].search_count(
            [('model_id.model', 'ilike', 'amunet.woo')])
        self.assertEqual(cron_count, 0)

    def test_backend_is_get_only(self):
        Backend = self.env['amunet.woo.backend']
        self.assertFalse(hasattr(Backend, 'action_sync_stock'))
        self.assertFalse(hasattr(Backend, '_sync_stock'))
        self.assertFalse(hasattr(Backend, '_cron_sync_stock'))
        self.assertTrue(hasattr(Backend, '_wc_get'))

    def test_logs_are_immutable_for_users(self):
        log = self.env['amunet.woo.sync.log'].create({
            'backend_id': self.backend.id,
            'operation': 'csv_import',
            'state': 'success',
            'message': 'corrida de prueba',
        })
        admin_user = self.env['res.users'].create({
            'name': 'Administrador Woo inmutable',
            'login': 'woo_log_admin_test',
            'group_ids': [(6, 0, [
                self.env.ref(
                    'amunet_woocommerce.group_woo_admin').id,
            ])],
        })
        # Ni el administrador del módulo puede editar o borrar bitácora (ACL).
        from odoo.exceptions import AccessError
        with self.assertRaises(AccessError):
            log.with_user(admin_user).check_access('write')
        with self.assertRaises(AccessError):
            log.with_user(admin_user).check_access('unlink')
        self.assertTrue(log.display_label)
