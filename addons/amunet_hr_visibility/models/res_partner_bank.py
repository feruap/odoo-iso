# -*- coding: utf-8 -*-
from odoo import models


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    def name_create(self, name):
        # El widget many2many_tags no pasa default_* a name_create automáticamente.
        # Lo tomamos explícitamente del contexto para que partner_id (campo requerido) se llene.
        partner_id = self.env.context.get('default_partner_id')
        if partner_id:
            record = self.create({'acc_number': name, 'partner_id': partner_id})
            return record.id, record.display_name
        return super().name_create(name)
