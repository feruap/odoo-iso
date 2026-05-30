# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AmunetEquipmentCalibration(models.Model):
    _name = 'amunet.equipment.calibration'
    _description = 'Certificado de Calibracion de Equipo'
    _order = 'calibration_date desc, id desc'

    equipment_id = fields.Many2one(
        'amunet.equipment', string='Equipo', required=True, ondelete='cascade')

    calibration_date = fields.Date(
        string='Fecha de Calibracion', required=True,
        default=fields.Date.context_today)
    expiration_date = fields.Date(string='Fecha de Vencimiento', required=True)

    certificate_file = fields.Binary(
        string='Certificado PDF (Laboratorio)', attachment=True)
    certificate_filename = fields.Char(string='Nombre Archivo')

    lab_name = fields.Char(string='Laboratorio Emisor / Proveedor')
    notes = fields.Text(string='Observaciones')
    approved_by_id = fields.Many2one(
        'res.users', string='Aprobado por', readonly=True, copy=False)
    approved_date = fields.Datetime(
        string='Fecha de aprobacion', readonly=True, copy=False)

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Aprobado'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='draft', required=True)

    @api.constrains('calibration_date', 'expiration_date')
    def _check_dates(self):
        for record in self:
            if (
                record.expiration_date
                and record.calibration_date
                and record.expiration_date <= record.calibration_date
            ):
                raise ValidationError(
                    "La Fecha de Vencimiento debe ser posterior a la Fecha de Calibracion.")

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_action_approve': _('Aprobar certificado de calibracion'),
        }

    def _amunet_signature_required_procedures(self):
        self.ensure_one()
        return self.equipment_id.procedure_ids.filtered('active')

    def _check_can_approve(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_("Solo se puede aprobar un certificado en Borrador."))
            if not record.certificate_file:
                raise UserError(_("Adjunta el certificado PDF del laboratorio antes de aprobar."))
            if not record.lab_name:
                raise UserError(_("Captura el laboratorio emisor/proveedor antes de aprobar."))

    def action_approve(self):
        self.ensure_one()
        self._check_can_approve()
        return self.env['amunet.generic.signature.wizard'].open_for(
            self,
            '_signature_action_approve',
            _('Aprobar certificado de calibracion'),
            _('Firma de aprobacion del certificado de %s.') % self.equipment_id.display_name,
        )

    def _signature_action_approve(self):
        self.ensure_one()
        self._check_can_approve()
        for record in self:
            record.with_context(amunet_calibration_signature_write=True).write({
                'state': 'done',
                'approved_by_id': self.env.user.id,
                'approved_date': fields.Datetime.now(),
            })
            if record.expiration_date and record.expiration_date >= fields.Date.today():
                if record.equipment_id.state == 'out_of_service':
                    record.equipment_id.write({'state': 'active'})
                    record.equipment_id.message_post(body=_(
                        "Equipo reactivado automaticamente al aprobar la calibracion "
                        "valida hasta %s.") % record.expiration_date)

    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'

    def action_draft(self):
        for record in self:
            record.state = 'draft'

    def _has_approval_signature_values(self, vals):
        return (
            vals.get('state') == 'done'
            or {'approved_by_id', 'approved_date'}.intersection(vals)
        )

    @api.model_create_multi
    def create(self, vals_list):
        if (
            not self.env.context.get('amunet_calibration_signature_write')
            and not self.env.su
        ):
            for vals in vals_list:
                if self._has_approval_signature_values(vals):
                    raise UserError(_(
                        'La aprobacion de certificados de calibracion solo '
                        'puede registrarse desde el wizard de firma electronica.'))
        return super().create(vals_list)

    def write(self, vals):
        if (
            self._has_approval_signature_values(vals)
            and not self.env.context.get('amunet_calibration_signature_write')
            and not self.env.su
        ):
            raise UserError(_(
                'La aprobacion de certificados de calibracion solo puede '
                'registrarse desde el wizard de firma electronica.'))
        return super().write(vals)
