# -*- coding: utf-8 -*-
from odoo import models, _


class AmunetDocumentoExt(models.Model):
    _inherit = 'amunet.documento'

    def action_open_sugerencia_wizard(self):
        """Abre un nuevo control de cambios general pre-llenado con los datos del documento."""
        self.ensure_one()
        nombre = '%s — %s' % (self.codigo, self.name) if self.codigo else self.name
        return {
            'name': _('Control de cambios: %s') % self.codigo,
            'type': 'ir.actions.act_window',
            'res_model': 'amunet.cc.general',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_nombre_documento': nombre,
                'default_tipo_pno': True,
            },
        }
