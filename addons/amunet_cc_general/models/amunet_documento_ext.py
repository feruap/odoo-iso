# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AmunetDocumentoExt(models.Model):
    _inherit = 'amunet.documento'

    cc_id_pendiente = fields.Many2one(
        'amunet.cc.general',
        string='Control de cambios',
        domain=[('state', '=', 'aceptado')],
        help='Selecciona el CC autorizado que respalda esta nueva versión',
    )

    @api.onchange('cc_id_pendiente')
    def _onchange_cc_id_pendiente(self):
        if self.cc_id_pendiente:
            cc = self.cc_id_pendiente
            self.cc_referencia_pendiente = cc.name
            if cc.estado_propuesto and not self.descripcion_cambio_pendiente:
                self.descripcion_cambio_pendiente = cc.estado_propuesto
            if cc.justificacion and not self.justificacion_pendiente:
                self.justificacion_pendiente = cc.justificacion

    def action_nueva_version_wizard(self):
        self.ensure_one()
        return {
            'name': _('Generar nueva versión'),
            'type': 'ir.actions.act_window',
            'res_model': 'amunet.nueva.version.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_documento_id': self.id},
        }

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
