from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

NIVEL_SELECTION = [
    ('alto', 'Alto riesgo'),
    ('medio', 'Riesgo medio'),
    ('bajo', 'Bajo riesgo'),
    ('ninguno', 'Sin riesgo'),
]


def _nivel_npr(npm):
    if npm == 0:
        return 'ninguno'
    elif npm <= 8:
        return 'bajo'
    elif npm <= 63:
        return 'medio'
    return 'alto'


class AmunetRiskAnalysis(models.Model):
    _name = 'amunet.risk.analysis'
    _description = 'Análisis de Riesgos AMEF'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha desc, id desc'

    name = fields.Char(string='Folio', readonly=True, copy=False, default='Nuevo')
    titulo = fields.Char(string='Título / Proceso / Producto', required=True, tracking=True)
    tipo = fields.Selection([
        ('proceso', 'Proceso'),
        ('producto', 'Producto'),
        ('sistema', 'Sistema'),
        ('area', 'Área'),
        ('otro', 'Otro'),
    ], string='Tipo', required=True, default='proceso', tracking=True)
    area_id = fields.Many2one(
        'amunet.desviacion.area', string='Área / Departamento', tracking=True)
    fecha = fields.Date(string='Fecha', default=fields.Date.today, required=True, tracking=True)
    responsable_id = fields.Many2one(
        'res.users', string='Responsable',
        default=lambda self: self.env.user, required=True, tracking=True)
    alcance = fields.Text(string='Alcance del análisis')

    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('revision', 'En revisión'),
        ('autorizacion', 'En autorización'),
        ('aprobado', 'Aprobado'),
    ], string='Estado', default='borrador', tracking=True)

    revisor_id = fields.Many2one(
        'res.users', string='Revisor del área',
        help='Jefe o responsable del área que revisará técnicamente el análisis.')
    reviso_id = fields.Many2one('res.users', string='Revisó', readonly=True)
    fecha_revisa = fields.Datetime(string='Fecha de revisión', readonly=True)

    linea_ids = fields.One2many(
        'amunet.risk.analysis.linea', 'analisis_id', string='Modos de falla')
    observaciones = fields.Text(string='Observaciones generales')

    firma_id = fields.Many2one('res.users', string='Autorizó', readonly=True)
    fecha_firma = fields.Datetime(string='Fecha de autorización', readonly=True)

    total_lineas = fields.Integer(compute='_compute_resumen', store=True)
    total_alto = fields.Integer(compute='_compute_resumen', store=True, string='Alto riesgo')
    total_medio = fields.Integer(compute='_compute_resumen', store=True, string='Riesgo medio')
    total_bajo = fields.Integer(compute='_compute_resumen', store=True, string='Bajo riesgo')

    criteria_ids = fields.Many2many(
        'amunet.risk.matrix', compute='_compute_criteria', string='Criterios NPR')

    def _compute_criteria(self):
        criterios = self.env['amunet.risk.matrix'].search([], order='npr_min')
        for rec in self:
            rec.criteria_ids = criterios

    @api.depends('linea_ids.nivel_riesgo')
    def _compute_resumen(self):
        for rec in self:
            rec.total_lineas = len(rec.linea_ids)
            rec.total_alto = len(rec.linea_ids.filtered(lambda l: l.nivel_riesgo == 'alto'))
            rec.total_medio = len(rec.linea_ids.filtered(lambda l: l.nivel_riesgo == 'medio'))
            rec.total_bajo = len(rec.linea_ids.filtered(lambda l: l.nivel_riesgo == 'bajo'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'amunet.risk.analysis') or 'Nuevo'
        return super().create(vals_list)

    def action_enviar_revision(self):
        self.ensure_one()
        if not self.linea_ids:
            raise UserError('Agrega al menos un modo de falla antes de enviar a revisión.')
        if not self.revisor_id:
            raise UserError('Selecciona el revisor del área antes de enviar a revisión.')
        self.write({'state': 'revision'})
        self.message_post(
            body=(f'El análisis <b>{self.name}</b> — {self.titulo} ha sido enviado a revisión.<br/>'
                  f'Por favor revísalo y marca como revisado cuando esté listo.'),
            partner_ids=[self.revisor_id.partner_id.id],
            message_type='email',
            subtype_xmlid='mail.mt_comment',
        )

    def action_marcar_revisado(self):
        self.ensure_one()
        if self.state != 'revision':
            raise UserError('El análisis debe estar en revisión.')
        self.write({
            'state': 'autorizacion',
            'reviso_id': self.env.user.id,
            'fecha_revisa': fields.Datetime.now(),
        })
        group = self.env.ref(
            'amunet_documentos.group_responsable_sanitario', raise_if_not_found=False)
        if group:
            autorizadores = self.env['res.users'].search([('group_ids', 'in', [group.id])])
            partners = autorizadores.mapped('partner_id')
        else:
            partners = self.env['res.partner']
        self.message_post(
            body=(f'El análisis <b>{self.name}</b> — {self.titulo} ha sido revisado por '
                  f'{self.reviso_id.name} y está pendiente de autorización.'),
            partner_ids=partners.ids,
            message_type='email',
            subtype_xmlid='mail.mt_comment',
        )

    def action_autorizar(self):
        self.ensure_one()
        if self.state != 'autorizacion':
            raise UserError('El análisis debe estar en autorización antes de autorizarse.')
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_autorizar', 'Autorización del análisis de riesgos')

    def _signature_autorizar(self):
        self.ensure_one()
        self.write({
            'state': 'aprobado',
            'firma_id': self.env.user.id,
            'fecha_firma': fields.Datetime.now(),
        })
        # Notificar a elaboró y revisó
        notificados = (self.responsable_id | self.reviso_id).mapped('partner_id')
        self.message_post(
            body=(f'El análisis <b>{self.name}</b> — {self.titulo} ha sido autorizado por '
                  f'{self.firma_id.name}. Queda vigente.'),
            partner_ids=notificados.ids,
            message_type='email',
            subtype_xmlid='mail.mt_comment',
        )
        # Notificar individualmente a cada responsable de acción
        responsables = self.linea_ids.filtered(
            lambda l: l.responsable_accion_id and l.accion
        ).mapped('responsable_accion_id')
        for usuario in responsables:
            acciones = self.linea_ids.filtered(
                lambda l: l.responsable_accion_id == usuario and l.accion)
            filas = ''.join(
                f'<li><b>{l.elemento}</b>: {l.accion}'
                f'{" — Fecha compromiso: <b>" + str(l.fecha_compromiso) + "</b>" if l.fecha_compromiso else ""}'
                f'</li>'
                for l in acciones
            )
            self.message_post(
                body=(f'El análisis de riesgos <b>{self.name}</b> — {self.titulo} '
                      f'ha sido autorizado y tienes acción(es) asignada(s):<ul>{filas}</ul>'
                      f'Por favor da seguimiento en el sistema.'),
                partner_ids=[usuario.partner_id.id],
                message_type='email',
                subtype_xmlid='mail.mt_comment',
            )

    def _amunet_signature_allowed_methods(self):
        return {'_signature_autorizar': 'Autorización del análisis de riesgos'}

    def action_regresar_borrador(self):
        self.ensure_one()
        if self.state == 'aprobado':
            raise UserError('No se puede regresar a borrador un análisis ya aprobado.')
        self.write({'state': 'borrador'})


class AmunetRiskAnalysisLinea(models.Model):
    _name = 'amunet.risk.analysis.linea'
    _description = 'Línea AMEF — Modo de Falla'
    _order = 'analisis_id, sequence, id'

    analisis_id = fields.Many2one(
        'amunet.risk.analysis', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)

    elemento = fields.Char(
        string='Elemento / Función', required=True,
        help="Parte específica del proceso, producto o sistema que se analiza:\n"
             "• Proceso → paso o actividad (ej. 'Pesado de materia prima', 'Sellado de membrana')\n"
             "• Producto → componente del dispositivo (ej. 'Membrana de nitrocelulosa', 'Conjugado de oro')\n"
             "• Sistema/Área → equipo o instalación (ej. 'Balanza analítica', 'Cuarto limpio ISO 7')\n\n"
             "Pregúntate: ¿en qué parte específica puede ocurrir el modo de falla?")
    modo_falla = fields.Char(
        string='Modo de falla potencial',
        help="¿De qué manera puede fallar el elemento en cumplir su función?\n"
             "• 'Peso fuera de especificación'\n"
             "• 'Sellado incompleto'\n"
             "• 'Resultado falso negativo'\n"
             "• 'Etiqueta ilegible o incorrecta'")
    efecto = fields.Char(
        string='Efecto del fallo',
        help="Consecuencia del modo de falla sobre el paciente, el usuario o la calidad del producto:\n"
             "• 'Diagnóstico incorrecto para el paciente'\n"
             "• 'Lote rechazado o reprocesado'\n"
             "• 'Incumplimiento regulatorio'\n"
             "• 'Contaminación del producto'")
    causa = fields.Char(
        string='Causa del fallo',
        help="Mecanismo o razón raíz que origina el modo de falla:\n"
             "• 'Calibración incorrecta del equipo'\n"
             "• 'Operador no capacitado'\n"
             "• 'Materia prima fuera de especificación'\n"
             "• 'Falta de mantenimiento preventivo'")
    controles_actuales = fields.Char(string='Controles actuales')

    severidad = fields.Integer(
        string='S', default=1,
        help="Severidad del efecto si el fallo ocurre (1 = mínima, 5 = máxima):\n"
             "1 — Sin impacto perceptible\n"
             "2 — Impacto menor, detectable internamente\n"
             "3 — Efecto moderado, requiere reproceso\n"
             "4 — Efecto grave, puede afectar la calidad del resultado\n"
             "5 — Crítico: riesgo para el paciente o incumplimiento regulatorio")
    ocurrencia = fields.Integer(
        string='O', default=1,
        help="Frecuencia con que ocurre la causa del fallo (1 = muy rara, 5 = muy frecuente):\n"
             "1 — Muy improbable (nunca ha ocurrido)\n"
             "2 — Remota (una vez en varios años)\n"
             "3 — Ocasional (algunas veces al año)\n"
             "4 — Frecuente (varias veces al mes)\n"
             "5 — Muy frecuente (ocurre regularmente)")
    detectabilidad = fields.Integer(
        string='D', default=1,
        help="Probabilidad de NO detectar el fallo antes de que llegue al siguiente paso o al cliente\n"
             "(1 = casi seguro que se detecta, 5 = prácticamente indetectable):\n"
             "1 — Detección casi segura (controles robustos, 100% automatizados)\n"
             "2 — Alta probabilidad de detección\n"
             "3 — Probabilidad media de detección\n"
             "4 — Baja probabilidad de detección\n"
             "5 — Sin control de detección existente")

    npm = fields.Integer(string='NPR', compute='_compute_npr', store=True)
    nivel_riesgo = fields.Selection(
        NIVEL_SELECTION, string='Nivel', compute='_compute_npr', store=True)

    accion = fields.Char(string='Acción recomendada')
    responsable_accion_id = fields.Many2one('res.users', string='Responsable acción')
    fecha_compromiso = fields.Date(string='Fecha compromiso')
    estado_accion = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En proceso'),
        ('completada', 'Completada'),
    ], string='Estado acción', default='pendiente')

    @api.depends('severidad', 'ocurrencia', 'detectabilidad')
    def _compute_npr(self):
        for rec in self:
            s = rec.severidad or 0
            o = rec.ocurrencia or 0
            d = rec.detectabilidad or 0
            rec.npm = s * o * d
            rec.nivel_riesgo = _nivel_npr(rec.npm)

    @api.constrains('severidad', 'ocurrencia', 'detectabilidad')
    def _check_escala(self):
        for rec in self:
            for campo, val in [('Severidad', rec.severidad),
                               ('Ocurrencia', rec.ocurrencia),
                               ('Detectabilidad', rec.detectabilidad)]:
                if val and not (1 <= val <= 5):
                    raise ValidationError(_('{} debe estar entre 1 y 5.').format(campo))
