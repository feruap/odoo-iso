# -*- coding: utf-8 -*-
"""Firma de Almacen para descontar el material conciliado.

Confirmar la conciliacion dejo de ser un cambio de estado: ahora descuenta
inventario y no se puede deshacer. Por eso se firma, y se firma viendo los
numeros -- un "estas seguro?" pelado se acepta en automatico y no protege nada.
"""
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AmunetConciliacionFirmaWizard(models.TransientModel):
    _name = 'amunet.conciliacion.firma.wizard'
    _description = 'Firma de Almacen para descontar el material conciliado'

    production_id = fields.Many2one('mrp.production', required=True, readonly=True)
    resumen_html = fields.Html(string='Se va a descontar', readonly=True)
    pin = fields.Char(string='PIN o contraseña', password=True)

    @api.model
    def abrir_para(self, production):
        wizard = self.create([{
            'production_id': production.id,
            'resumen_html': self._resumen(production),
        }])
        return {
            'type': 'ir.actions.act_window',
            'name': _('Confirmar conciliación'),
            'res_model': self._name,
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    @api.model
    def _resumen(self, production):
        filas = production._amunet_resumen_conciliacion()
        if not filas:
            return '<p>Esta orden no tiene material surtido que descontar.</p>'
        cuerpo = []
        for f in filas:
            cuerpo.append(
                '<tr><td>%(prod)s</td>'
                '<td style="text-align:right">%(sur).4g</td>'
                '<td style="text-align:right"><b>%(uso).4g</b></td>'
                '<td style="text-align:right">%(reg).4g</td></tr>' % {
                    'prod': f['producto'], 'sur': f['surtido'],
                    'uso': f['usado'], 'reg': f['regresa']})
        return (
            '<table class="table table-sm">'
            '<thead><tr><th>Material</th><th style="text-align:right">Surtido</th>'
            '<th style="text-align:right">Usado</th>'
            '<th style="text-align:right">Regresa</th></tr></thead>'
            '<tbody>%s</tbody></table>' % ''.join(cuerpo))

    def action_confirmar(self):
        self.ensure_one()
        if not self.pin:
            raise UserError(_('Escribe tu PIN o tu contraseña para firmar.'))
        # Misma validacion que el resto de las firmas del sistema: PIN o
        # contrasena. Ver amunet.quality.signature.pin.
        Pin = self.env['amunet.quality.signature.pin']
        if not Pin.amunet_validar_credencial(self.pin):
            raise UserError(_(
                'La firma no coincide.\n\n'
                'Puedes usar tu PIN de firma o la contraseña con la que entras '
                'al sistema.'))
        production = self.production_id
        production.with_context(
            amunet_conciliacion_firmada=True).action_complete_reconciliation()
        production.sudo().message_post(body=_(
            'Conciliación firmada por <b>%s</b>: el material se descontó del '
            'inventario y el sobrante regresó al almacén.'
        ) % self.env.user.name)
        return {'type': 'ir.actions.act_window_close'}
