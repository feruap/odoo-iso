# -*- coding: utf-8 -*-
# Wizard de FIRMA de aprobación de un manual (ISO 13485 / CFR 21 Part 11).
# Pide el PIN/contraseña del usuario de Calidad y, si es válido, aprueba y
# firma el manual (delega en amunet.doc.compartida.action_aprobar_firmar).
from odoo import models, fields


class DocFirmaWizard(models.TransientModel):
    _name = 'amunet.doc.firma.wizard'
    _description = 'Firma de aprobación de manual'

    doc_id = fields.Many2one(
        'amunet.doc.compartida', string='Documento', required=True, readonly=True)
    doc_name = fields.Char(related='doc_id.name', string='Manual', readonly=True)
    password = fields.Char(string='PIN / Contraseña', required=True)

    def action_firmar(self):
        self.ensure_one()
        self.doc_id.action_aprobar_firmar(self.password)
        return {'type': 'ir.actions.act_window_close'}
