# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AmunetNuevaVersionWizard(models.TransientModel):
    _name = 'amunet.nueva.version.wizard'
    _description = 'Asistente para generar nueva versión de documento controlado'

    documento_id = fields.Many2one('amunet.documento', required=True, readonly=True)
    documento_codigo = fields.Char(related='documento_id.codigo', readonly=True)
    documento_nombre = fields.Char(related='documento_id.name', readonly=True)

    cc_id = fields.Many2one(
        'amunet.cc.general',
        string='Control de cambios autorizado',
        domain=[('state', '=', 'aceptado')],
        required=True,
        help='Selecciona el CC autorizado que respalda esta nueva versión',
    )
    descripcion_cambio = fields.Text(string='Descripción del cambio')
    justificacion = fields.Text(string='Justificación')

    @api.onchange('cc_id')
    def _onchange_cc_id(self):
        if self.cc_id:
            if self.cc_id.estado_propuesto:
                self.descripcion_cambio = self.cc_id.estado_propuesto
            if self.cc_id.justificacion:
                self.justificacion = self.cc_id.justificacion

    def action_confirmar(self):
        self.ensure_one()
        doc = self.documento_id
        doc.sudo().write({
            'cc_referencia_pendiente': self.cc_id.name,
            'descripcion_cambio_pendiente': self.descripcion_cambio,
            'justificacion_pendiente': self.justificacion,
        })
        return doc.action_nueva_version()
