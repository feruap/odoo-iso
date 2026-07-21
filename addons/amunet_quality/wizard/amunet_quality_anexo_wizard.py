# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AmunetQualityAnexoWizard(models.TransientModel):
    _name = 'amunet.quality.anexo.wizard'
    _description = 'Captura de Datos del Anexo'

    check_id = fields.Many2one('amunet.quality.check', required=True, ondelete='cascade')

    # Encabezados (solo lectura, vienen del QC)
    anexo_titulo      = fields.Char(related='check_id.anexo_titulo', readonly=True)
    col1_header       = fields.Char(related='check_id.anexo_col1_header', readonly=True)
    col2_header       = fields.Char(related='check_id.anexo_col2_header', readonly=True)
    col3_header       = fields.Char(related='check_id.anexo_col3_header', readonly=True)
    col4_header       = fields.Char(related='check_id.anexo_col4_header', readonly=True)
    col5_header       = fields.Char(related='check_id.anexo_col5_header', readonly=True)
    col6_header       = fields.Char(related='check_id.anexo_col6_header', readonly=True)
    col7_header       = fields.Char(related='check_id.anexo_col7_header', readonly=True)

    # Las líneas apuntan directamente al QC — se guardan en la BD al confirmar
    line_ids = fields.One2many(
        'amunet.quality.anexo.line',
        'check_id',
        related='check_id.anexo_line_ids',
        readonly=False,
    )

    @api.model
    def action_open_for_check(self, check_id):
        wizard = self.create({'check_id': check_id})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Datos del Anexo',
            'res_model': 'amunet.quality.anexo.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_cerrar(self):
        return {'type': 'ir.actions.act_window_close'}
