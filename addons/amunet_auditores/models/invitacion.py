import uuid
from odoo import api, fields, models


class AmunetAuditorInvitacion(models.Model):
    _name = 'amunet.auditor.invitacion'
    _description = 'Invitación a convocatoria de auditores'
    _order = 'convocatoria_id, usuario_id'

    convocatoria_id = fields.Many2one(
        'amunet.auditor.convocatoria', required=True, ondelete='cascade')
    usuario_id = fields.Many2one('res.users', string='Empleado', required=True)
    token = fields.Char(required=True, copy=False, index=True, readonly=True)
    respuesta = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('interesado', 'Interesado'),
        ('no_interesado', 'No interesado'),
    ], default='pendiente', readonly=True)
    fecha_respuesta = fields.Datetime(string='Fecha de respuesta', readonly=True)
    candidato_id = fields.Many2one(
        'amunet.auditor.candidato', string='Candidato creado', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('token'):
                vals['token'] = uuid.uuid4().hex
        return super().create(vals_list)

    def action_agregar_candidato(self):
        self.ensure_one()
        if self.candidato_id:
            return
        candidato = self.env['amunet.auditor.candidato'].create({
            'convocatoria_id': self.convocatoria_id.id,
            'usuario_id': self.usuario_id.id,
        })
        self.candidato_id = candidato
