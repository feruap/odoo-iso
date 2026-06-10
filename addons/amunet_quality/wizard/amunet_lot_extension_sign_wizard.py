# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


_ROLE_LABELS = {
    'quality': 'Calidad',
    'sanitary': 'Responsable Sanitario',
    'warehouse': 'Almacén',
}

_ROLE_NEXT_STATE = {
    'quality': 'draft',
    'sanitary': 'signed_quality',
    'warehouse': 'signed_sanitary',
}


class AmunetLotExtensionSignWizard(models.TransientModel):
    _name = 'amunet.lot.extension.sign.wizard'
    _description = 'Firma de extensión de caducidad'

    extension_id = fields.Many2one(
        'amunet.lot.extension',
        string='Extensión',
        required=True,
        readonly=True,
    )
    signature_role = fields.Selection([
        ('quality', 'Calidad'),
        ('sanitary', 'Responsable Sanitario'),
        ('warehouse', 'Almacén'),
    ], string='Rol de firma', required=True, readonly=True)

    lot_name = fields.Char(related='extension_id.lot_id.name', string='Lote', readonly=True)
    product_name = fields.Char(
        related='extension_id.lot_id.product_id.display_name',
        string='Producto', readonly=True,
    )
    expiration_date_before = fields.Date(
        related='extension_id.expiration_date_before',
        string='Caducidad original', readonly=True,
    )
    expiration_date_after = fields.Date(
        related='extension_id.expiration_date_after',
        string='Nueva caducidad', readonly=True,
    )
    months_extended = fields.Integer(
        related='extension_id.months_extended',
        string='Meses a extender', readonly=True,
    )

    password = fields.Char(
        string='PIN / Contraseña',
        required=True,
        help='Ingresa tu PIN de firma o contraseña de Odoo.',
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        ctx = self.env.context
        if ctx.get('default_extension_id'):
            ext = self.env['amunet.lot.extension'].browse(ctx['default_extension_id'])
            role = ctx.get('default_signature_role', 'quality')
            required_state = _ROLE_NEXT_STATE.get(role, 'draft')
            if ext.state != required_state:
                raise ValidationError(
                    'No es posible firmar como %s en este momento. '
                    'Estado actual: %s' % (
                        _ROLE_LABELS.get(role, role), ext.state
                    )
                )
        return res

    def action_confirm_sign(self):
        self.ensure_one()
        ext = self.extension_id
        role = self.signature_role

        try:
            if role == 'quality':
                ext.action_sign_quality(self.password)
            elif role == 'sanitary':
                ext.action_sign_sanitary(self.password)
            elif role == 'warehouse':
                ext.action_sign_warehouse(self.password)
        except Exception as e:
            raise ValidationError(str(e))

        return {'type': 'ir.actions.act_window_close'}
