# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import ValidationError


class ClabeWizard(models.TransientModel):
    _name = 'amunet.clabe.wizard'
    _description = 'Capturar CLABE de empleado nuevo'

    employee_id = fields.Many2one('hr.employee', required=True, readonly=True)
    clabe = fields.Char('Número CLABE', required=True)

    def action_guardar(self):
        self.ensure_one()
        emp = self.employee_id
        if emp.bank_account_ids:
            raise ValidationError(_(
                "Este empleado ya tiene una cuenta registrada. "
                "Para cambiarla usa Control de Nómina → Cambios de cuenta bancaria."
            ))
        clabe = (self.clabe or '').strip()
        if not clabe:
            raise ValidationError(_("Escribe el número CLABE."))
        partner = emp.work_contact_id or emp.address_home_id
        if not partner:
            raise ValidationError(_(
                "El empleado no tiene un contacto de trabajo asignado. "
                "Guarda primero sus datos generales y vuelve a intentarlo."
            ))
        bank = self.env['res.partner.bank'].sudo().with_context(nomina_approved=True).create({
            'acc_number': clabe,
            'partner_id': partner.id,
        })
        emp.sudo().write({'bank_account_ids': [(4, bank.id)]})
        return {'type': 'ir.actions.act_window_close'}
