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

    puntaje_total = fields.Float(
        compute='_compute_puntaje', store=True, string='Puntaje', digits=(4, 1))
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

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        criterios = self.env['amunet.auditor.criterio'].search(
            [('active', '=', True)], order='categoria, secuencia, name')
        for rec in records:
            if not rec.evaluacion_ids:
                self.env['amunet.auditor.evaluacion'].create([{
                    'candidato_id': rec.id,
                    'criterio_id': c.id,
                    'evaluador_id': self.env.user.id,
                } for c in criterios])
        return records

    @api.depends('evaluacion_ids.calificacion_int')
    def _compute_puntaje(self):
        for rec in self:
            evals = rec.evaluacion_ids
            evals_num = evals.filtered(lambda e: e.criterio_id.tipo == 'numerica')
            total = sum(evals_num.mapped('calificacion_int'))
            maximo = len(evals_num) * 5
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
    _order = 'candidato_id, criterio_secuencia, criterio_id'

    candidato_id = fields.Many2one(
        'amunet.auditor.candidato', required=True, ondelete='cascade')
    criterio_id = fields.Many2one(
        'amunet.auditor.criterio', string='Criterio', required=True,
        domain=[('active', '=', True)])
    criterio_tipo = fields.Selection(
        related='criterio_id.tipo', string='Tipo', readonly=True, store=True)
    criterio_secuencia = fields.Integer(
        related='criterio_id.secuencia', string='Secuencia', store=True)
    criterio_descripcion = fields.Text(
        related='criterio_id.descripcion', string='Preguntas guía', readonly=True)
    evaluador_id = fields.Many2one(
        'res.users', string='Evaluador',
        default=lambda self: self.env.user)
    calificacion = fields.Selection([
        ('1', '1 — Muy bajo'),
        ('2', '2 — Bajo'),
        ('3', '3 — Medio'),
        ('4', '4 — Alto'),
        ('5', '5 — Muy alto'),
    ], string='Calificación manual')
    respuesta_abierta = fields.Text(string='Respuesta')
    observaciones = fields.Text(string='Observaciones')
    fecha = fields.Date(default=fields.Date.today, readonly=True)
    respuesta_ids = fields.One2many(
        'amunet.auditor.respuesta.eval', 'evaluacion_id', string='Respuestas')
    tiene_preguntas = fields.Boolean(
        compute='_compute_tiene_preguntas', string='Tiene preguntas')

    def _compute_tiene_preguntas(self):
        for rec in self:
            rec.tiene_preguntas = bool(rec.criterio_id.pregunta_ids)

    @api.depends('respuesta_ids.puntaje', 'calificacion')
    def _compute_calificacion_int(self):
        for rec in self:
            scores = rec.respuesta_ids.filtered(lambda r: r.puntaje).mapped('puntaje')
            if scores:
                rec.calificacion_int = sum(scores) / len(scores)
            elif rec.calificacion:
                rec.calificacion_int = float(rec.calificacion)
            else:
                rec.calificacion_int = 0.0

    calificacion_int = fields.Float(
        compute='_compute_calificacion_int', store=True, digits=(4, 1))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            preguntas = rec.criterio_id.pregunta_ids.sorted('secuencia')
            if preguntas:
                self.env['amunet.auditor.respuesta.eval'].create([{
                    'evaluacion_id': rec.id,
                    'pregunta_id': p.id,
                } for p in preguntas])
        return records

    def action_abrir_evaluacion_criterio(self):
        self.ensure_one()
        preguntas = self.criterio_id.pregunta_ids.sorted('secuencia')
        ya_ids = self.respuesta_ids.mapped('pregunta_id').ids
        faltantes = preguntas.filtered(lambda p: p.id not in ya_ids)
        if faltantes:
            self.env['amunet.auditor.respuesta.eval'].create([{
                'evaluacion_id': self.id,
                'pregunta_id': p.id,
            } for p in faltantes])
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'amunet.auditor.evaluacion',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {'dialog_size': 'medium'},
        }
