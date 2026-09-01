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
    fecha_entrevista = fields.Date(
        string='Fecha de entrevistas', tracking=True)
    _HORAS = [(h, h) for h in [
        '07:00','07:30','08:00','08:30','09:00','09:30','10:00','10:30',
        '11:00','11:30','12:00','12:30','13:00','13:30','14:00','14:30',
        '15:00','15:30','16:00','16:30','17:00','17:30','18:00','18:30','19:00',
    ]]
    hora_inicio_entrevista = fields.Selection(_HORAS, string='Hora de inicio')
    hora_fin_entrevista = fields.Selection(_HORAS, string='Hora de fin')
    lugar_entrevista = fields.Char(
        string='Lugar', default='Instalaciones Amunet')
    vacantes = fields.Integer(
        string='Vacantes', default=3, required=True)
    area_ids = fields.Many2many(
        'amunet.area', 'convocatoria_area_rel', 'convocatoria_id', 'area_id',
        string='Áreas a auditar')
    correo_contacto = fields.Char(
        string='Correo de contacto', default='documentacion@amunet.com.mx')

    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('publicada', 'Publicada'),
        ('en_proceso', 'En proceso'),
        ('cerrada', 'Cerrada'),
        ('cancelada', 'Cancelada'),
    ], default='borrador', tracking=True)

    fecha_publicacion = fields.Date(string='Fecha de publicación', readonly=True)
    fecha_cierre = fields.Date(string='Fecha de cierre', readonly=True)

    destinatario_ids = fields.Many2many(
        'res.users', string='Enviar invitación a',
        domain=[('share', '=', False), ('active', '=', True)],
        help='Personas que recibirán el correo de convocatoria al publicar.')
    candidato_ids = fields.One2many(
        'amunet.auditor.candidato', 'convocatoria_id', string='Candidatos')
    invitacion_ids = fields.One2many(
        'amunet.auditor.invitacion', 'convocatoria_id', string='Invitaciones')
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

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        enviados = 0
        for usuario in self.destinatario_ids:
            if not usuario.email:
                continue
            inv = self.env['amunet.auditor.invitacion'].create({
                'convocatoria_id': self.id,
                'usuario_id': usuario.id,
            })
            url_si = '%s/auditores/respuesta/%s/si' % (base_url, inv.token)
            url_no = '%s/auditores/respuesta/%s/no' % (base_url, inv.token)
            body_html = """
<p>Hola <b>%s</b>,</p>
<p>Amunet lanza una convocatoria para la <b>selección y formación de Auditores Internos</b>
(%s). Si te interesa participar, haz clic en uno de los botones:</p>
<p style="margin:24px 0;text-align:center;">
  <a href="%s" style="background:#28a745;color:#fff;padding:12px 28px;border-radius:6px;
     text-decoration:none;font-weight:bold;margin-right:12px;">✅ Estoy interesado</a>
  <a href="%s" style="background:#6c757d;color:#fff;padding:12px 28px;border-radius:6px;
     text-decoration:none;font-weight:bold;">❌ No me interesa</a>
</p>
<p><b>Fecha límite de inscripción:</b> %s</p>
<p>Si tienes dudas, escríbenos a <a href="mailto:%s">%s</a>.</p>
<p>Saludos,<br/>Área de Documentación — Amunet</p>
""" % (usuario.name, self.name, url_si, url_no,
       self.fecha_limite or 'por confirmar',
       self.correo_contacto or '', self.correo_contacto or '')
            self.env['mail.mail'].sudo().create({
                'subject': 'Convocatoria Auditores Internos — %s' % self.name,
                'body_html': body_html,
                'email_to': usuario.email,
                'auto_delete': True,
            }).send()
            enviados += 1

        self.write({'state': 'publicada', 'fecha_publicacion': fields.Date.today()})
        self.message_post(
            body='Convocatoria publicada. %s%s' % (
                'Invitaciones enviadas a %d persona(s). ' % enviados if enviados else 'Sin destinatarios seleccionados. ',
                'Fecha límite: %s' % self.fecha_limite,
            )
        )

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
