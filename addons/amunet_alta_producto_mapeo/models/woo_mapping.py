# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import UserError


class WooProductMapping(models.Model):
    _inherit = 'amunet.woo.product.mapping'

    def action_proponer_alta(self):
        """Crea una PROPUESTA de alta pre-llenada desde este mapeo Woo.
        La propuesta la aprueban Mery o Fernando (grupo material manager);
        al aprobar se crea el producto con clave y clasificacion.
        """
        self.ensure_one()
        if self.product_id:
            raise UserError(_(
                'Este mapeo ya tiene un producto Odoo (%s). No hace falta proponer alta.'
            ) % self.product_id.display_name)
        Proposal = self.env['amunet.marketplace.product.proposal']
        nombre = self.woo_name or self.woo_sku or _('Producto nuevo desde Woo')
        prop = Proposal.create({
            'name': nombre,
            'requester_id': self.env.user.id,
            'request_type': 'general',
            'clave_propuesta': self.woo_sku or False,
            'origen_mapeo_id': self.id,
            'justification': _(
                'Alta propuesta desde el mapeo Woo. SKU: %(sku)s | ID Woo: %(wid)s | '
                'Nombre en tienda: %(nom)s'
            ) % {'sku': self.woo_sku or '-', 'wid': self.woo_product_id or '-',
                 'nom': self.woo_name or '-'},
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Propuesta de alta'),
            'res_model': 'amunet.marketplace.product.proposal',
            'res_id': prop.id,
            'view_mode': 'form',
            'target': 'current',
        }
