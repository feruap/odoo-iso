from odoo import fields, models, _
from odoo.exceptions import UserError


class AmunetTraspasoRechazo(models.TransientModel):
    _name = 'amunet.traspaso.distribucion.rechazo'
    _description = 'Motivo de rechazo del traspaso a Distribucion'

    traspaso_id = fields.Many2one(
        'amunet.traspaso.distribucion', string='Solicitud', required=True)
    motivo = fields.Text(string='Motivo del rechazo', required=True)

    def action_confirmar(self):
        self.ensure_one()
        motivo = (self.motivo or '').strip()
        if len(motivo) < 10:
            raise UserError(_(
                'Escribe el motivo del rechazo. Un numero de orden no es un '
                'motivo: explica que tiene el material.'))
        return self.traspaso_id._rechazar(motivo)
