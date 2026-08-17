from odoo import fields, models


class AmunetAuditorRespuestaEval(models.Model):
    _name = 'amunet.auditor.respuesta.eval'
    _description = 'Respuesta a pregunta de opción múltiple en evaluación'
    _order = 'evaluacion_id, pregunta_id'

    evaluacion_id = fields.Many2one(
        'amunet.auditor.evaluacion', required=True, ondelete='cascade')
    pregunta_id = fields.Many2one(
        'amunet.auditor.pregunta', required=True, readonly=True)
    pregunta_name = fields.Char(
        related='pregunta_id.name', string='Pregunta', readonly=True)
    opcion_id = fields.Many2one(
        'amunet.auditor.opcion', string='Respuesta seleccionada',
        domain="[('pregunta_id', '=', pregunta_id)]")
    respuesta_abierta = fields.Text(string='Respuesta')
    puntaje = fields.Integer(
        related='opcion_id.puntaje', string='Puntaje', store=True, readonly=True)
