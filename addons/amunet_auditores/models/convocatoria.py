from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AmunetAuditorConvocatoria(models.Model):
    _name = 'amunet.auditor.convocatoria'
    _description = 'Convocatoria para auditores internos (PNODC-003)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_emision desc, id desc'

    name = fields.Char(
        string='Folio', readonly=True, copy=False, default='Nuevo')
    fecha_emision = fields.Date(
        string='Fecha de emisión', default=fields.Date.today, required=True, tracking=True)
    fecha_limite = fields.Date(
        string='Fecha límite de inscripción', required=True, tracking=True)
    fecha_entrevista = fields.Datetime(
        string='Fecha y hora de entrevistas', tracking=True)
    lugar_entrevista = fields.Char(
        string='Lugar', default='Instalaciones Amunet')
    vacantes = fields.Integer(
        string='Vacantes', default=3, required=True)
    correo_contacto = fields.Char(
        string='Correo de contacto', default='auditorias@amunet.com.mx')

    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('publicada', 'Publicada'),
        ('en_proceso', 'En proceso'),
        ('cerrada', 'Cerrada'),
        ('cancelada', 'Cancelada'),
    ], default='borrador', tracking=True)

    fecha_publicacion = fields.Date(string='Fecha de publicación', readonly=True)
    fecha_cierre = fields.Date(string='Fecha de cierre', readonly=True)

    candidato_ids = fields.One2many(
        'amunet.auditor.candidato', 'convocatoria_id', string='Candidatos')
    candidato_count = fields.Integer(
        compute='_compute_conteos', store=True, string='Candidatos')
    seleccionados_count = fields.Integer(
        compute='_compute_conteos', store=True, string='Seleccionados')

    objetivo = fields.Text(
        string='Objetivo',
        default='Seleccionar y formar auditores internos para el Sistema de Gestión de '
                'Calidad de Amunet S.A. de C.V., conforme al Plan de Auditoría Interna '
                'y a los requerimientos del PNODC-003.')
    funciones = fields.Text(
        string='Funciones y responsabilidades',
        default='- Planificar y conducir auditorías asignadas.\n'
                '- Documentar hallazgos y no conformidades.\n'
                '- Reportar resultados al auditor líder.\n'
                '- Mantener confidencialidad de la información.\n'
                '- Dar seguimiento a acciones correctivas.')
    beneficios = fields.Text(
        string='Beneficios',
        default='- Desarrollo de competencias en auditoría de calidad.\n'
                '- Constancia oficial de participación.\n'
                '- Reconocimiento dentro de la organización.')

    formacion_academica = fields.Text(
        string='Formación académica',
        default='- Licenciatura o técnico en área afín (Química, Biología, Bioquímica,\n'
                '  Ingeniería Industrial, Calidad o similar).\n'
                '- Deseable: curso o certificación en auditorías internas ISO 13485\n'
                '  o sistemas de gestión de calidad.')

    @api.depends('candidato_ids.estado')
    def _compute_conteos(self):
        for rec in self:
            rec.candidato_count = len(rec.candidato_ids)
            rec.seleccionados_count = len(
                rec.candidato_ids.filtered(lambda c: c.estado == 'seleccionado'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'amunet.auditor.convocatoria') or 'Nuevo'
        return super().create(vals_list)

    def action_publicar(self):
        self.ensure_one()
        if self.state != 'borrador':
            raise UserError('Solo se pueden publicar convocatorias en borrador.')
        self.write({'state': 'publicada', 'fecha_publicacion': fields.Date.today()})
        self.message_post(body='Convocatoria publicada. Fecha límite: %s' % self.fecha_limite)

    def action_iniciar_proceso(self):
        self.ensure_one()
        if not self.candidato_ids:
            raise UserError('No hay candidatos inscritos.')
        self.write({'state': 'en_proceso'})

    def action_cerrar(self):
        self.ensure_one()
        self.write({'state': 'cerrada', 'fecha_cierre': fields.Date.today()})
        self.message_post(body='Convocatoria cerrada.')

    def action_cancelar(self):
        self.write({'state': 'cancelada'})
