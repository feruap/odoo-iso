# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'amunet_governance')
class TestSystemGovernance(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({'name': 'Producto DCC prueba'})

    def test_system_change_requires_risk_and_validation(self):
        self.env.user.sudo().write({
            'group_ids': [(4, self.env.ref('amunet_quality.group_quality_manager').id)],
        })
        change = self.env['amunet.change.control'].create({
            'title': 'Cambio de sistema sin evidencia',
            'request_type': 'system_change',
            'scope': 'permanent',
            'product_id': self.product.id,
            'rationale': 'Cambio requerido para trazabilidad.',
            'risk_level': 'high',
            'regulatory_impact': 'both',
        })

        with self.assertRaises(UserError):
            change.action_submit()

        change.write({
            'risk_assessment': 'Riesgo controlado con pruebas en staging.',
            'validation_evidence': 'Validado en staging por usuario de prueba.',
        })
        change.action_submit()
        self.assertEqual(change.state, 'evaluation')

    def test_user_group_changes_create_permission_audit_log(self):
        user = self.env['res.users'].create({
            'name': 'Auditado permisos',
            'login': 'auditado.permisos@amunet.invalid',
            'email': 'auditado.permisos@amunet.invalid',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        logs_before = self.env['amunet.permission.audit.log'].search_count([
            ('target_user_id', '=', user.id),
        ])

        user.write({'group_ids': [(4, self.env.ref('base.group_system').id)]})

        logs_after = self.env['amunet.permission.audit.log'].search_count([
            ('target_user_id', '=', user.id),
        ])
        self.assertGreater(logs_after, logs_before)
