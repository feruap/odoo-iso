# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import UserError


class RevisionMapeoLinea(models.Model):
    _inherit = 'amunet.revision.mapeo.linea'

    def action_proponer_alta(self):
        """Desde una linea 'nuevo' de la revision (producto publicado en la
        tienda que no existe en Odoo), crea una PROPUESTA de alta pre-llenada.
        La aprueban Mery o Fernando; al aprobar se crea el producto.
        """
        self.ensure_one()
        if self.tipo != 'nuevo':
            raise UserError(_(
                'Solo se propone alta para lineas de tipo "nuevo" '
                '(publicado en la tienda sin producto en Odoo).'))
        Proposal = self.env['amunet.marketplace.product.proposal']
        prop = Proposal.create({
            'name': self.woo_name or self.woo_sku or _('Producto nuevo desde Woo'),
            'requester_id': self.env.user.id,
            'request_type': 'general',
            'clave_propuesta': self.woo_sku or False,
            'justification': _(
                'Alta propuesta desde la Revision del mapeo. SKU: %(sku)s | '
                'ID Woo: %(wid)s | Nombre en tienda: %(nom)s'
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
