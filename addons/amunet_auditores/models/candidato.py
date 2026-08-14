from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AmunetAuditorCandidato(models.Model):
    _name = 'amunet.auditor.candidato'
    _description = 'Candidato a auditor interno'
    _order = 'puntaje_total desc, usuario_id'

    convocatoria_id = fields.Many2one(
        'amunet.auditor.convocatoria', required=True, ondelete='cascade')
    usuario_id = fields.Many2one(
        'res.users', string='Candidato', required=True,
        domain=[('share', '=', False)])

    evaluacion_ids = fields.One2many(
        'amunet.auditor.evaluacion', 'candidato_id', string='Evaluaciones')

    puntaje_total = fields.Integer(
        compute='_compute_puntaje', store=True, string='Puntaje')
    porcentaje = fields.Float(
        compute='_compute_puntaje', store=True, string='%')
    criterios_count = fields.Integer(
        compute='_compute_puntaje', store=True, string='Criterios evaluados')

    estado = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('evaluado', 'Evaluado'),
        ('seleccionado', 'Seleccionado'),
        ('rechazado', 'Rechazado'),
        ('espera', 'Lista de espera'),
    ], default='pendiente', tracking=True)

    es_lider = fields.Boolean(string='Auditor líder')
    tipo_auditor = fields.Selection([
        ('formacion', 'En formación'),
        ('interno', 'Auditor interno'),
        ('lider', 'Auditor líder'),
    ], compute='_compute_tipo', store=True, string='Tipo')

    observaciones = fields.Text()
    justificacion = fields.Text(string='Justificación')

    @api.depends('evaluacion_ids.calificacion_int')
    def _compute_puntaje(self):
        for rec in self:
            evals = rec.evaluacion_ids
            total = sum(evals.mapped('calificacion_int'))
            maximo = len(evals) * 5
            rec.criterios_count = len(evals)
            rec.puntaje_total = total
            rec.porcentaje = (total / maximo * 100) if maximo else 0.0

    @api.depends('puntaje_total', 'estado', 'es_lider')
    def _compute_tipo(self):
        for rec in self:
            if rec.estado != 'seleccionado':
                rec.tipo_auditor = False
            elif rec.es_lider:
                rec.tipo_auditor = 'lider'
            elif rec.puntaje_total >= 18:
                rec.tipo_auditor = 'interno'
            else:
                rec.tipo_auditor = 'formacion'

    def action_seleccionar(self):
        self.ensure_one()
        vacantes = self.convocatoria_id.vacantes
        if vacantes:
            ya = self.convocatoria_id.candidato_ids.filtered(
                lambda c: c.estado == 'seleccionado')
            if len(ya) >= vacantes:
                raise UserError(
                    'Ya se cubrieron las %s vacantes de esta convocatoria.' % vacantes)
        self.write({'estado': 'seleccionado'})

    def action_rechazar(self):
        self.write({'estado': 'rechazado'})

    def action_espera(self):
        self.write({'estado': 'espera'})

    def action_designar_lider(self):
        self.convocatoria_id.candidato_ids.write({'es_lider': False})
        self.write({'es_lider': True, 'estado': 'seleccionado'})

    def action_abrir_evaluacion(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'amunet.auditor.candidato',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }


class AmunetAuditorEvaluacion(models.Model):
    _name = 'amunet.auditor.evaluacion'
    _description = 'Evaluación de criterio por candidato'
    _order = 'candidato_id, criterio_id'

    candidato_id = fields.Many2one(
        'amunet.auditor.candidato', required=True, ondelete='cascade')
    criterio_id = fields.Many2one(
        'amunet.auditor.criterio', string='Criterio', required=True,
        domain=[('active', '=', True)])
    evaluador_id = fields.Many2one(
        'res.users', string='Evaluador',
        default=lambda self: self.env.user)
    calificacion = fields.Selection([
        ('1', '1 — Muy bajo'),
        ('2', '2 — Bajo'),
        ('3', '3 — Medio'),
        ('4', '4 — Alto'),
        ('5', '5 — Muy alto'),
    ], string='Calificación', required=True, default='3')
    observaciones = fields.Text()
    fecha = fields.Date(default=fields.Date.today, readonly=True)

    @api.depends('calificacion')
    def _compute_calificacion_int(self):
        for rec in self:
            rec.calificacion_int = int(rec.calificacion) if rec.calificacion else 0

    calificacion_int = fields.Integer(compute='_compute_calificacion_int', store=True)
