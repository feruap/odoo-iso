# -*- coding: utf-8 -*-

from markupsafe import escape

from odoo import models, fields, api, _
from odoo.exceptions import AccessDenied, ValidationError


class AmunetQualityLotReleaseWizard(models.TransientModel):
    _name = 'amunet.quality.lot.release.wizard'
    _description = 'Liberación final de lote'

    lot_id = fields.Many2one(
        'stock.lot',
        string='Lote',
        required=True,
        readonly=True,
    )

    password = fields.Char(
        string='Contraseña / PIN',
        required=True,
        help='Ingrese su contraseña o PIN de firma.',
    )

    release_notes = fields.Text(
        string='Notas de liberación',
        help='Notas opcionales que quedarán dentro del snapshot DHR.',
    )

    validation_summary = fields.Html(
        string='Validación',
        compute='_compute_validation_summary',
        sanitize=False,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id and self.env.context.get('active_model') == 'stock.lot':
            res['lot_id'] = active_id
        return res

    @api.depends('lot_id')
    def _compute_validation_summary(self):
        for wizard in self:
            if not wizard.lot_id:
                wizard.validation_summary = ''
                continue

            blockers = wizard.lot_id._get_lot_release_blockers()
            if blockers:
                items = ''.join('<li>%s</li>' % escape(item) for item in blockers)
                wizard.validation_summary = (
                    '<div class="alert alert-warning">'
                    '<strong>No se puede liberar todavía.</strong>'
                    '<ul>%s</ul>'
                    '</div>'
                ) % items
            else:
                release_check = wizard.lot_id._get_lot_release_quality_check()
                wizard.validation_summary = (
                    '<div class="alert alert-success">'
                    '<strong>Lote listo para liberación final.</strong><br/>'
                    'QC de liberación: %s'
                    '</div>'
                ) % escape(release_check.display_name)

    def _validate_release_signer(self):
        allowed = (
            self.env.user.has_group('amunet_quality.group_quality_sanitary') or
            self.env.user.has_group('amunet_quality.group_quality_manager') or
            self.env.user.has_group('base.group_system')
        )
        if not allowed:
            self.lot_id._log_lot_release_event(
                success=False,
                message='Usuario sin grupo autorizado intentó liberar lote',
                new_value='FALLIDA: usuario sin permisos',
            )
            raise AccessDenied(_(
                'Solo Responsable Sanitario, Manager de Calidad o Administrador '
                'pueden liberar lotes.'
            ))

    def _validate_credentials(self, release_check):
        signature_wizard = self.env['amunet.quality.signature.wizard'].new({
            'check_ids': [(6, 0, release_check.ids)],
            'password': self.password,
            'signature_type': 'authorized',
        })
        if not signature_wizard._validate_credentials(self.password):
            self.lot_id._log_lot_release_event(
                success=False,
                message='Credenciales inválidas en liberación final de lote',
                new_value='FALLIDA: credenciales inválidas',
            )
            raise ValidationError(_('La contraseña o PIN es incorrecto.'))

    def action_confirm_release(self):
        self.ensure_one()
        self._validate_release_signer()

        blockers = self.lot_id._get_lot_release_blockers()
        if blockers:
            raise ValidationError('\n'.join(blockers))

        release_check = self.lot_id._get_lot_release_quality_check()
        self._validate_credentials(release_check)
        self.lot_id._action_release_lot(notes=self.release_notes)

        return {'type': 'ir.actions.act_window_close'}
