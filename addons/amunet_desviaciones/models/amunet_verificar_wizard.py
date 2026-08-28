from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AmunetDesviacionVerificarWizard(models.TransientModel):
    _name = 'amunet.desviacion.verificar.wizard'
    _description = 'Verificar efectividad de acción correctiva / preventiva'

    accion_id = fields.Many2one('amunet.desviacion.accion', required=True)
    descripcion_accion = fields.Text(related='accion_id.descripcion', readonly=True)
    evidencia_efectividad = fields.Text(
        string='¿Fue efectiva la acción?',
        required=True,
    )

    def action_confirmar(self):
        self.ensure_one()
        accion = self.accion_id
        accion.write({
            'state': 'verificada',
            'evidencia_efectividad': self.evidencia_efectividad,
        })
        accion.desviacion_id._message_log(
            body=_('<p><b>%s</b> verificó la acción: %s</p>'
                   '<p><b>Evidencia de efectividad:</b> %s</p>') % (
                self.env.user.name,
                accion.descripcion or '',
                self.evidencia_efectividad,
            )
        )
