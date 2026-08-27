# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class AmunetMoBajaWizard(models.TransientModel):
    """Popup para dar de baja un lote no conforme: captura motivo + firma (PIN)
    en un solo dialogo. Solo Responsable Sanitario. Al confirmar, segrega el
    terminado a APT/Rechazo y cierra la MO (ver mrp.production._amunet_baja_rechazada_firma)."""
    _name = 'amunet.mo.baja.wizard'
    _description = 'Baja de lote no conforme (motivo + firma)'

    production_id = fields.Many2one(
        'mrp.production', string='Orden', required=True, readonly=True)
    motivo = fields.Text(string='Motivo de la baja', required=True)
    password = fields.Char(string='PIN / Contraseña', required=True)

    def action_confirm(self):
        self.ensure_one()
        mo = self.production_id
        if not self.env.user.has_group('amunet_quality.group_quality_sanitary'):
            raise UserError(_('Solo el Responsable Sanitario puede dar de baja un lote no conforme.'))
        if mo.quality_analysis_status != 'rejected':
            raise UserError(_('Solo se puede dar de baja un lote cuyo análisis fue RECHAZADO.'))
        if not (self.motivo or '').strip():
            raise UserError(_('El motivo de la baja es obligatorio.'))
        # Firma: PIN de firma o contraseña de Odoo (mismo validador que las demas firmas)
        if not self.env['amunet.generic.signature.wizard']._validate_credentials(self.password):
            raise UserError(_('PIN o contraseña incorrecta.'))
        mo.sudo().amunet_baja_motivo = self.motivo
        mo._amunet_baja_rechazada_firma()
        return {'type': 'ir.actions.act_window_close'}
