# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from markupsafe import Markup

from odoo import models, fields, api
from odoo.exceptions import UserError


class AmunetLotExtension(models.Model):
    _name = 'amunet.lot.extension'
    _description = 'Extensión de caducidad por reanálisis'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Folio',
        readonly=True,
        copy=False,
        default='Nueva',
    )
    lot_id = fields.Many2one(
        'stock.lot',
        string='Lote',
        required=True,
        readonly=True,
        ondelete='cascade',
        tracking=True,
    )
    product_id = fields.Many2one(
        related='lot_id.product_id',
        string='Producto',
        readonly=True,
        store=True,
    )
    state = fields.Selection([
        ('draft', 'Solicitud'),
        ('signed_quality', 'Firmado — Calidad'),
        ('signed_sanitary', 'Firmado — Resp. Sanitario'),
        ('done', 'Aprobado'),
        ('cancelled', 'Cancelado'),
    ], string='Estado', default='draft', required=True, tracking=True, copy=False)

    months_extended = fields.Integer(
        string='Meses a extender',
        required=True,
        tracking=True,
    )
    expiration_date_before = fields.Date(
        string='Caducidad original',
        readonly=True,
        tracking=True,
    )
    expiration_date_after = fields.Date(
        string='Nueva caducidad',
        compute='_compute_expiration_date_after',
        store=True,
        tracking=True,
    )
    reanalysis_check_id = fields.Many2one(
        'amunet.quality.check',
        string='Reanálisis aprobado',
        readonly=True,
    )
    notes = fields.Text(string='Observaciones')

    quality_user_id = fields.Many2one('res.users', string='Firmó Calidad', readonly=True, copy=False)
    quality_date = fields.Datetime(string='Fecha firma Calidad', readonly=True, copy=False)

    sanitary_user_id = fields.Many2one('res.users', string='Firmó Resp. Sanitario', readonly=True, copy=False)
    sanitary_date = fields.Datetime(string='Fecha firma Resp. Sanitario', readonly=True, copy=False)

    warehouse_user_id = fields.Many2one('res.users', string='Firmó Almacén', readonly=True, copy=False)
    warehouse_date = fields.Datetime(string='Fecha firma Almacén', readonly=True, copy=False)

    @api.depends('expiration_date_before', 'months_extended')
    def _compute_expiration_date_after(self):
        for ext in self:
            if ext.expiration_date_before and ext.months_extended > 0:
                ext.expiration_date_after = ext.expiration_date_before + relativedelta(months=ext.months_extended)
            else:
                ext.expiration_date_after = ext.expiration_date_before

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == 'Nueva':
            vals['name'] = self.env['ir.sequence'].next_by_code('amunet.lot.extension') or 'Nueva'
        return super().create(vals)

    def _validate_pin(self, password):
        sig_wizard = self.env['amunet.quality.signature.wizard'].new({
            'password': password,
            'signature_type': 'authorized',
        })
        return sig_wizard._validate_credentials(password)

    def _log_extension_event(self, old_state, new_state, message):
        self.ensure_one()
        self.env['amunet.quality.audit.log'].sudo().create({
            'model_name': 'amunet.lot.extension',
            'res_id': self.id,
            'res_name': self.name,
            'field_name': 'state',
            'field_description': 'Extensión de caducidad',
            'old_value': old_state,
            'new_value': new_state,
            'justification': message,
            'user_id': self.env.user.id,
        })

    def action_sign_quality(self, password):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError('Esta solicitud ya fue firmada por Calidad.')
        if not self.months_extended or self.months_extended <= 0:
            raise UserError('Ingresa los meses de extensión antes de firmar.')
        if not self._validate_pin(password):
            raise UserError('PIN o contraseña incorrectos.')
        old_state = self.state
        self.write({
            'state': 'signed_quality',
            'quality_user_id': self.env.user.id,
            'quality_date': fields.Datetime.now(),
        })
        self._log_extension_event(old_state, 'signed_quality',
                                  'Firmado Calidad: %s' % self.env.user.name)
        self.message_post(
            body=Markup('Firma de <b>Calidad</b> registrada por <b>%s</b>.' % self.env.user.name),
            message_type='notification',
        )

    def action_sign_sanitary(self, password):
        self.ensure_one()
        if self.state != 'signed_quality':
            raise UserError('Primero debe firmar Calidad.')
        if not self._validate_pin(password):
            raise UserError('PIN o contraseña incorrectos.')
        old_state = self.state
        self.write({
            'state': 'signed_sanitary',
            'sanitary_user_id': self.env.user.id,
            'sanitary_date': fields.Datetime.now(),
        })
        self._log_extension_event(old_state, 'signed_sanitary',
                                  'Firmado Resp. Sanitario: %s' % self.env.user.name)
        self.message_post(
            body=Markup('Firma de <b>Responsable Sanitario</b> registrada por <b>%s</b>.' % self.env.user.name),
            message_type='notification',
        )

    def action_sign_warehouse(self, password):
        self.ensure_one()
        if self.state != 'signed_sanitary':
            raise UserError('Primero deben firmar Calidad y Responsable Sanitario.')
        if not self._validate_pin(password):
            raise UserError('PIN o contraseña incorrectos.')
        old_state = self.state
        self.write({
            'state': 'done',
            'warehouse_user_id': self.env.user.id,
            'warehouse_date': fields.Datetime.now(),
        })
        self._log_extension_event(old_state, 'done',
                                  'Firmado Almacén: %s — Nueva caducidad: %s' % (
                                      self.env.user.name, self.expiration_date_after))
        self.message_post(
            body=Markup(
                'Firma de <b>Almacén</b> registrada por <b>%s</b>.<br/>'
                'Caducidad: <b>%s → %s</b>' % (
                    self.env.user.name,
                    self.expiration_date_before,
                    self.expiration_date_after,
                )
            ),
            message_type='notification',
        )
        self._apply_extension_to_lot()

    def _apply_extension_to_lot(self):
        self.ensure_one()
        lot = self.lot_id
        lot.with_context(skip_lot_release_lock=True).write({
            'expiration_date': self.expiration_date_after,
        })
        # removal_date y reanalysis_date se recalculan solos por _compute_reanalysis_date
        lot.message_post(
            body=Markup(
                'Caducidad extendida por reanálisis. Extensión: <b>%s</b><br/>'
                'Nueva caducidad: <b>%s</b> (+%d mes(es))' % (
                    self.name, self.expiration_date_after, self.months_extended,
                )
            ),
            message_type='notification',
        )

    def _open_sign_wizard(self, role):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Firma electrónica',
            'res_model': 'amunet.lot.extension.sign.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_extension_id': self.id,
                'default_signature_role': role,
            },
        }

    def action_open_sign_quality_wizard(self):
        return self._open_sign_wizard('quality')

    def action_open_sign_sanitary_wizard(self):
        return self._open_sign_wizard('sanitary')

    def action_open_sign_warehouse_wizard(self):
        return self._open_sign_wizard('warehouse')

    def action_cancel(self):
        for ext in self:
            if ext.state == 'done':
                raise UserError('No se puede cancelar una extensión ya aplicada.')
            old_state = ext.state
            ext.write({'state': 'cancelled'})
            ext._log_extension_event(old_state, 'cancelled',
                                     'Cancelado por %s' % self.env.user.name)
