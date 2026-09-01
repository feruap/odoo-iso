from odoo import api, fields, models


class AmunetAuditorPregunta(models.Model):
    _name = 'amunet.auditor.pregunta'
    _description = 'Pregunta de evaluación para criterio de auditor'
    _order = 'criterio_id, secuencia, id'

    criterio_id = fields.Many2one(
        'amunet.auditor.criterio', required=True, ondelete='cascade')
    name = fields.Char(string='Pregunta', required=True)
    secuencia = fields.Integer(default=10)
    opcion_ids = fields.One2many(
        'amunet.auditor.opcion', 'pregunta_id', string='Opciones de respuesta')


class AmunetAuditorOpcion(models.Model):
    _name = 'amunet.auditor.opcion'
    _description = 'Opción de respuesta para pregunta de evaluación'
    _order = 'pregunta_id, puntaje desc'
    _rec_name = 'display_name'

    pregunta_id = fields.Many2one(
        'amunet.auditor.pregunta', required=True, ondelete='cascade')
    puntaje = fields.Integer(string='Puntaje', required=True, default=3)
    descripcion = fields.Text(string='Descripción', required=True)
    display_name = fields.Char(
        compute='_compute_display_name', store=True)

    @api.depends('puntaje', 'descripcion')
    def _compute_display_name(self):
        for r in self:
            r.display_name = '%d — %s' % (r.puntaje, r.descripcion or '')
