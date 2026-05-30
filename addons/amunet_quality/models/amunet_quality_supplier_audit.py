# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AmunetQualitySupplierAudit(models.Model):
    _name = 'amunet.quality.supplier.audit'
    _description = 'Auditoria a Proveedor'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'audit_date desc'

    name = fields.Char(
        string='Referencia', required=True, copy=False,
        readonly=True, default='Nuevo')
    partner_id = fields.Many2one(
        'res.partner',
        string='Proveedor',
        required=True,
        domain=[('supplier_rank', '>', 0)],
        tracking=True
    )
    audit_date = fields.Date(
        string='Fecha Auditoria', required=True,
        default=fields.Date.context_today, tracking=True)
    auditor_id = fields.Many2one(
        'res.users', string='Auditor',
        default=lambda self: self.env.user, tracking=True)
    result = fields.Selection([
        ('pass', 'Aprobado'),
        ('conditional', 'Condicional'),
        ('fail', 'Rechazado')
    ], string='Resultado', required=True, tracking=True)
    report_file = fields.Binary(string='Informe de Auditoria')
    report_filename = fields.Char(string='Nombre Archivo')
    notes = fields.Text(string='Observaciones')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Realizada'),
        ('cancel', 'Cancelada')
    ], string='Estado', default='draft', tracking=True)
    confirmed_by_id = fields.Many2one(
        'res.users', string='Confirmado por', readonly=True, copy=False)
    confirmed_date = fields.Datetime(
        string='Fecha confirmacion', readonly=True, copy=False)

    def _has_confirmation_signature_values(self, vals):
        return (
            vals.get('state') == 'done'
            or {'confirmed_by_id', 'confirmed_date'}.intersection(vals)
        )

    @api.model_create_multi
    def create(self, vals_list):
        if (
            not self.env.context.get('amunet_supplier_audit_signature_write')
            and not self.env.su
        ):
            for vals in vals_list:
                if self._has_confirmation_signature_values(vals):
                    raise UserError(_(
                        'La confirmacion de auditorias de proveedor solo '
                        'puede registrarse desde el wizard de firma electronica.'))
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code(
                        'amunet.quality.supplier.audit') or 'AUD-PROV'
                )
        return super().create(vals_list)

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_action_confirm': _('Confirmar auditoria de proveedor'),
        }

    def _check_can_confirm(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Solo se confirma una auditoria en Borrador.'))
            if not record.result:
                raise UserError(_('Capture el resultado de la auditoria.'))
            if not record.report_file:
                raise UserError(_('Adjunte el informe de auditoria antes de confirmar.'))

    def action_confirm(self):
        self.ensure_one()
        self._check_can_confirm()
        return self.env['amunet.generic.signature.wizard'].open_for(
            self,
            '_signature_action_confirm',
            _('Confirmar auditoria de proveedor'),
            _('Firma de cierre de auditoria de proveedor %s.') % self.name,
        )

    def _signature_action_confirm(self):
        self.ensure_one()
        self._check_can_confirm()
        status = {
            'pass': 'approved',
            'conditional': 'conditional',
            'fail': 'rejected',
        }.get(self.result)
        if status:
            self.partner_id.write({
                'quality_status': status,
                'last_audit_date': self.audit_date,
            })
        self.with_context(amunet_supplier_audit_signature_write=True).write({
            'state': 'done',
            'confirmed_by_id': self.env.user.id,
            'confirmed_date': fields.Datetime.now(),
        })
        return True

    def write(self, vals):
        if (
            self._has_confirmation_signature_values(vals)
            and not self.env.context.get('amunet_supplier_audit_signature_write')
            and not self.env.su
        ):
            raise UserError(_(
                'La confirmacion de auditorias de proveedor solo puede '
                'registrarse desde el wizard de firma electronica.'))
        return super().write(vals)
