# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


AREA_SELECTION = [
    ('GE', 'Generales (PNOGE)'),
    ('PR', 'Produccion (PNOPR)'),
    ('CC', 'Control de Calidad (PNOCC)'),
    ('AS', 'Aseguramiento de Calidad (PNOAS)'),
    ('AL', 'Almacen (PNOAL)'),
    ('IN', 'Ingenieria (PNOIN)'),
    ('RH', 'Recursos Humanos (PNORH)'),
    ('OTRO', 'Otra'),
]

CAMPOS_BLOQUEADOS_VIGENTE = (
    'codigo', 'name', 'tipo', 'area', 'version_actual',
    'archivo', 'archivo_filename', 'contenido_html',
    'seccion_objetivo', 'seccion_alcance', 'seccion_introduccion',
    'seccion_mision_vision', 'seccion_responsabilidades',
    'seccion_organigrama', 'seccion_terminos_definiciones',
    'seccion_condiciones_generales', 'seccion_formatos_derivados',
    'seccion_referencias', 'seccion_anexos',
    'elabora_id', 'fecha_elabora',
)


class AmunetDocumento(models.Model):
    _name = 'amunet.documento'
    _description = 'Documento Controlado (ISO 13485 4.2 / NOM-241-SSA1-2025)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'codigo'

    codigo = fields.Char(
        string='Codigo', required=True, copy=False,
        default='Nuevo', tracking=True,
        help='Clave alfanumerica unica. Ej. PNOGE-001.')
    name = fields.Char(string='Titulo', required=True, tracking=True)
    area = fields.Selection(
        AREA_SELECTION, string='Area', default='GE', tracking=True,
        help='Area responsable del documento.')
    tipo = fields.Selection([
        ('manual', 'Manual'),
        ('pno', 'PNO (Procedimiento Normalizado de Operacion)'),
        ('instructivo', 'Instructivo'),
        ('formato', 'Formato'),
        ('politica', 'Politica'),
        ('especificacion', 'Especificacion'),
        ('otro', 'Otro'),
    ], string='Tipo', default='pno', required=True, tracking=True)
    version_actual = fields.Char(string='Version actual', default='01', tracking=True)
    sustituye_version = fields.Char(
        string='Sustituye version', readonly=True,
        help='Version anterior que reemplaza esta version.')
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('en_revision', 'En revision'),
        ('vigente', 'Vigente'),
        ('obsoleto', 'Obsoleto'),
    ], string='Estado', default='borrador', tracking=True)
    responsable_id = fields.Many2one(
        'res.users', string='Responsable',
        default=lambda self: self.env.user, tracking=True,
        help='Dueno del documento que recibe las alertas de vigencia.')
    fecha_emision = fields.Date(
        string='Fecha de emision', readonly=True,
        help='Fecha en la que el documento entro en vigor.')
    fecha_vigencia = fields.Date(
        string='Proxima revision', tracking=True,
        help='Fecha en la que el documento debe revisarse o renovarse.')
    fecha_publicacion = fields.Date(string='Fecha de publicacion', readonly=True)
    archivo = fields.Binary(
        string='Archivo Word adjunto (opcional / legado)', attachment=True,
        help='Solo para documentos migrados desde Word. Para documentos nuevos usa el '
             'editor de contenido.')
    archivo_filename = fields.Char(string='Nombre de archivo')
    contenido_html = fields.Html(
        string='Contenido libre (otros tipos de documento)',
        sanitize=True,
        sanitize_tags=False,
        help='Solo para tipo "Otro" o documentos sin estructura. Para PNOs, Manuales e '
             'Instructivos usa las secciones estructuradas (Objetivo, Alcance, etc).')

    # ====================================================================
    # Secciones segun PNOGE-001 Anexo 2 (Estructura de los documentos)
    # ====================================================================
    seccion_objetivo = fields.Html(
        string='Objetivo', sanitize=True, sanitize_tags=False,
        help='Describe el proposito o razon de ser del documento.')
    seccion_alcance = fields.Html(
        string='Alcance', sanitize=True, sanitize_tags=False,
        help='Areas o procesos donde aplica el documento.')
    seccion_introduccion = fields.Html(
        string='Introduccion', sanitize=True, sanitize_tags=False,
        help='Solo Manuales. Resumen de lo que el lector encontrara.')
    seccion_mision_vision = fields.Html(
        string='Mision y Vision', sanitize=True, sanitize_tags=False,
        help='Solo Manuales.')
    seccion_responsabilidades = fields.Html(
        string='Responsabilidades', sanitize=True, sanitize_tags=False,
        help='Obligaciones por puesto o rol involucrado.')
    seccion_organigrama = fields.Html(
        string='Organigrama', sanitize=True, sanitize_tags=False,
        help='Solo Manuales (opcional).')
    seccion_terminos_definiciones = fields.Html(
        string='Terminos y definiciones', sanitize=True, sanitize_tags=False,
        help='Palabras, siglas o abreviaturas que aclarar.')
    seccion_condiciones_generales = fields.Html(
        string='Condiciones generales', sanitize=True, sanitize_tags=False,
        help='Indicaciones generales aplicables al documento.')
    # Desarrollo del proceso esta como One2many (actividad_ids) para usar la tabla
    seccion_formatos_derivados = fields.Html(
        string='Formatos derivados', sanitize=True, sanitize_tags=False,
        help='Formatos mencionados en el documento.')
    seccion_referencias = fields.Html(
        string='Referencias bibliograficas', sanitize=True, sanitize_tags=False,
        help='Normas, libros, articulos consultados. Cita NOM-241-SSA1-2025 cuando aplique.')
    seccion_anexos = fields.Html(
        string='Anexos', sanitize=True, sanitize_tags=False,
        help='Tablas, diagramas e informacion complementaria.')

    actividad_ids = fields.One2many(
        'amunet.documento.actividad', 'documento_id',
        string='Desarrollo del proceso',
        help='Tabla Actividad / Descripcion / Responsable / Registro segun PNOGE-001.')

    sugerencia_ids = fields.One2many(
        'amunet.documento.sugerencia', 'documento_id',
        string='Sugerencias de cambio')
    sugerencias_pendientes_count = fields.Integer(
        compute='_compute_sugerencias_pendientes_count', store=False,
        string='Sugerencias pendientes')

    # Tres firmas (PNOGE-001 Anexo 4): Elabora / Revisa / Autoriza
    elabora_id = fields.Many2one(
        'res.users', string='Elaboro',
        default=lambda self: self.env.user, tracking=True,
        help='Persona que elaboro el documento.')
    fecha_elabora = fields.Date(
        string='Fecha elaboracion', tracking=True,
        default=fields.Date.context_today)
    revisor_id = fields.Many2one(
        'res.users', string='Asignado para revisar', tracking=True,
        help='Persona que debe revisar el documento. Recibira una tarea en su bandeja.')
    autorizador_id = fields.Many2one(
        'res.users', string='Asignado para autorizar', tracking=True,
        help='Persona que debe autorizar el documento (Responsable Sanitario, Direccion). '
             'Recibira una tarea en su bandeja despues de la revision.')
    firma_revisa_id = fields.Many2one(
        'res.users', string='Firma de revision', readonly=True, tracking=True)
    fecha_revisa = fields.Date(string='Fecha de revision', readonly=True, tracking=True)
    firma_aprueba_id = fields.Many2one(
        'res.users', string='Firma de autorizacion', readonly=True, tracking=True,
        help='Responsable Sanitario / Auxiliar / Direccion General.')
    fecha_aprueba = fields.Date(string='Fecha de autorizacion', readonly=True, tracking=True)

    version_ids = fields.One2many(
        'amunet.documento.version', 'documento_id',
        string='Historial de versiones')
    distribucion_ids = fields.One2many(
        'amunet.documento.distribucion', 'documento_id',
        string='Distribucion')
    company_id = fields.Many2one(
        'res.company', string='Compania',
        default=lambda self: self.env.company)

    dias_a_vigencia = fields.Integer(
        string='Dias para revision',
        compute='_compute_dias_a_vigencia', store=False)

    # Politica de firmas aplicable y usuarios permitidos
    firma_config_id = fields.Many2one(
        'amunet.documento.firma.config',
        compute='_compute_firma_config',
        string='Politica de firmas aplicable', store=False)
    allowed_revisor_ids = fields.Many2many(
        'res.users', 'amunet_doc_allowed_revisor_rel', 'doc_id', 'user_id',
        compute='_compute_allowed_signers', store=False,
        string='Revisores autorizados')
    allowed_autorizador_ids = fields.Many2many(
        'res.users', 'amunet_doc_allowed_autorizador_rel', 'doc_id', 'user_id',
        compute='_compute_allowed_signers', store=False,
        string='Autorizadores autorizados')

    # Firmas snapshot (para migracion de PNOs ya firmados en papel/Word)
    firmas_snapshot = fields.Text(
        string='Firmas snapshot (migracion)',
        readonly=True,
        help='Firmas autografas capturadas del documento original al hacer la migracion inicial. '
             'A partir del proximo cambio, las firmas se generan electronicamente con clic.')

    # Campos para preparar la nueva version (se vacian al publicarla)
    descripcion_cambio_pendiente = fields.Text(
        string='Descripcion del cambio',
        help='Que cambio respecto a la version anterior. Obligatorio para publicar una nueva version.')
    justificacion_pendiente = fields.Text(
        string='Justificacion del cambio',
        help='Por que se cambia. Obligatorio para publicar una nueva version.')

    motivo_devolucion = fields.Text(
        string='Motivo para devolver',
        help='Que tiene que corregir el elaborador. Se manda como tarea pendiente y queda en el chat.')

    _sql_constraints = [
        ('codigo_uniq', 'unique(codigo)', 'El codigo del documento debe ser unico.'),
    ]

    @api.depends('fecha_vigencia')
    def _compute_dias_a_vigencia(self):
        today = fields.Date.context_today(self)
        for r in self:
            if r.fecha_vigencia:
                r.dias_a_vigencia = (r.fecha_vigencia - today).days
            else:
                r.dias_a_vigencia = 0

    @api.depends('sugerencia_ids.state')
    def _compute_sugerencias_pendientes_count(self):
        for r in self:
            r.sugerencias_pendientes_count = len(
                r.sugerencia_ids.filtered(lambda s: s.state == 'pendiente'))

    def action_open_sugerencia_wizard(self):
        self.ensure_one()
        return {
            'name': _('Sugerir cambio en %s') % self.codigo,
            'type': 'ir.actions.act_window',
            'res_model': 'amunet.documento.sugerencia',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_documento_id': self.id,
            },
        }

    @api.depends('area')
    def _compute_firma_config(self):
        Config = self.env['amunet.documento.firma.config']
        for r in self:
            r.firma_config_id = Config._find_for_area(r.area)

    @api.depends('firma_config_id',
                 'firma_config_id.revisor_user_ids',
                 'firma_config_id.autorizador_user_ids')
    def _compute_allowed_signers(self):
        for r in self:
            if r.firma_config_id and r.firma_config_id.revisor_user_ids:
                r.allowed_revisor_ids = r.firma_config_id.revisor_user_ids
            else:
                r.allowed_revisor_ids = self.env['res.users'].search([('share', '=', False)])
            if r.firma_config_id and r.firma_config_id.autorizador_user_ids:
                r.allowed_autorizador_ids = r.firma_config_id.autorizador_user_ids
            else:
                r.allowed_autorizador_ids = self.env['res.users'].search([('share', '=', False)])

    @api.onchange('area')
    def _onchange_area_aplicar_defaults(self):
        for r in self:
            config = self.env['amunet.documento.firma.config']._find_for_area(r.area)
            if not config:
                continue
            if config.revisor_default_id and not r.revisor_id:
                r.revisor_id = config.revisor_default_id
            if config.autorizador_default_id and not r.autorizador_id:
                r.autorizador_id = config.autorizador_default_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('codigo') or vals.get('codigo') == 'Nuevo':
                area = vals.get('area') or 'GE'
                seq_code = 'amunet.documento.%s' % area.lower()
                code = self.env['ir.sequence'].next_by_code(seq_code)
                if not code:
                    code = self.env['ir.sequence'].next_by_code('amunet.documento') or 'NUEVO'
                vals['codigo'] = code
        return super().create(vals_list)

    def write(self, vals):
        # Bloqueo de edicion cuando el documento esta Vigente (NOM-241 5.2.2.2)
        # Solo aplica si no estamos cambiando de estado.
        if vals.get('state') in (None, 'vigente'):
            tocados = set(CAMPOS_BLOQUEADOS_VIGENTE).intersection(vals.keys())
            if tocados:
                for r in self:
                    if r.state == 'vigente':
                        raise UserError(_(
                            'No puedes modificar %s mientras "%s" esta Vigente. '
                            'Genera una nueva version o pasalo a obsoleto primero.'
                        ) % (', '.join(sorted(tocados)), r.codigo))
        return super().write(vals)

    def _validar_estructura_pnoge_001(self):
        """Verifica que las secciones requeridas segun tipo (PNOGE-001 Anexo 2) tengan contenido."""
        self.ensure_one()
        # Si hay archivo Word adjunto y nada estructurado, asumimos documento migrado y solo
        # requerimos Objetivo + Alcance.
        def _vacio(html):
            txt = (html or '').replace('<p>', '').replace('</p>', '').replace('<br>', '').strip()
            return not txt or txt in ('&nbsp;', '<br/>', '<p><br></p>')
        requeridos = []
        if self.tipo == 'pno':
            requeridos = [
                ('seccion_objetivo', 'Objetivo'),
                ('seccion_alcance', 'Alcance'),
                ('seccion_responsabilidades', 'Responsabilidades'),
                ('seccion_terminos_definiciones', 'Terminos y definiciones'),
                ('seccion_condiciones_generales', 'Condiciones generales'),
                ('seccion_formatos_derivados', 'Formatos derivados'),
                ('seccion_referencias', 'Referencias bibliograficas'),
            ]
        elif self.tipo == 'manual':
            requeridos = [
                ('seccion_objetivo', 'Objetivo'),
                ('seccion_alcance', 'Alcance'),
                ('seccion_introduccion', 'Introduccion'),
                ('seccion_mision_vision', 'Mision y Vision'),
                ('seccion_terminos_definiciones', 'Terminos y definiciones'),
            ]
        elif self.tipo == 'instructivo':
            requeridos = [
                ('seccion_objetivo', 'Objetivo'),
                ('seccion_alcance', 'Alcance'),
                ('seccion_responsabilidades', 'Responsabilidades'),
                ('seccion_terminos_definiciones', 'Terminos y definiciones'),
                ('seccion_formatos_derivados', 'Formatos derivados'),
                ('seccion_referencias', 'Referencias bibliograficas'),
            ]
        else:
            # Politica, formato, especificacion, otro: solo objetivo y alcance si los hay,
            # o contenido libre.
            return
        # Si hay archivo Word, suavizamos: solo exigimos objetivo y alcance.
        if self.archivo:
            requeridos = [r for r in requeridos
                          if r[0] in ('seccion_objetivo', 'seccion_alcance')]
        faltantes = [label for (f, label) in requeridos if _vacio(getattr(self, f))]
        if self.tipo in ('pno', 'manual', 'instructivo') and not self.actividad_ids and not self.archivo:
            faltantes.append('Desarrollo del proceso (al menos una actividad)')
        if faltantes:
            raise UserError(_(
                'Faltan secciones obligatorias del documento segun PNOGE-001:\n- %s\n\n'
                'Captura el contenido en la pestana correspondiente antes de mandar a revision.'
            ) % '\n- '.join(faltantes))

    def action_en_revision(self):
        for r in self:
            secciones_text = ''.join([
                r.seccion_objetivo or '', r.seccion_alcance or '',
                r.seccion_introduccion or '', r.seccion_mision_vision or '',
                r.seccion_responsabilidades or '', r.seccion_organigrama or '',
                r.seccion_terminos_definiciones or '', r.seccion_condiciones_generales or '',
                r.seccion_formatos_derivados or '', r.seccion_referencias or '',
                r.seccion_anexos or '',
            ]).strip()
            tiene_contenido = r.archivo or (r.contenido_html or '').strip() or \
                              secciones_text or r.actividad_ids
            if not tiene_contenido:
                raise UserError(_(
                    'El documento esta vacio. Captura el contenido en las pestanas de secciones '
                    '(Objetivo, Alcance, Desarrollo del proceso, etc.) o adjunta el archivo Word si es migracion.'))
            r._validar_estructura_pnoge_001()
            if not r.elabora_id:
                raise UserError(_('Asigna quien elaboro el documento antes de mandarlo a revision.'))
            if not r.revisor_id:
                raise UserError(_('Asigna quien debe revisar el documento (campo "Asignado para revisar").'))
            if not r.autorizador_id:
                raise UserError(_('Asigna quien debe autorizar el documento (campo "Asignado para autorizar").'))
            # Validar contra politica de firmas
            if r.firma_config_id and r.firma_config_id.revisor_user_ids \
                    and r.revisor_id not in r.firma_config_id.revisor_user_ids:
                raise UserError(_(
                    'El revisor %s no esta autorizado para revisar documentos del area "%s" '
                    'segun la politica de firmas "%s". Elige a alguien de la lista permitida o '
                    'pide a un responsable que actualice la politica.'
                ) % (r.revisor_id.name, dict(r._fields['area'].selection).get(r.area, r.area),
                     r.firma_config_id.name))
            if r.firma_config_id and r.firma_config_id.autorizador_user_ids \
                    and r.autorizador_id not in r.firma_config_id.autorizador_user_ids:
                raise UserError(_(
                    'El autorizador %s no esta autorizado segun la politica de firmas "%s". '
                    'Elige a alguien de la lista permitida.'
                ) % (r.autorizador_id.name, r.firma_config_id.name))
            r.write({'state': 'en_revision'})
            r.message_subscribe(partner_ids=[r.revisor_id.partner_id.id,
                                              r.autorizador_id.partner_id.id])
            r.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('Revisar documento %s') % r.codigo,
                note=_(
                    '<p>Revisa el documento <b>%s</b> (%s v%s).</p>'
                    '<p>Si esta correcto, pulsa el boton <b>"Aprobar revision"</b>. '
                    'Si necesita cambios, devuelvelo a borrador.</p>'
                ) % (r.name, r.codigo, r.version_actual),
                user_id=r.revisor_id.id,
            )

    def action_aprobar_revision(self):
        for r in self:
            if r.state != 'en_revision':
                raise UserError(_('Solo se aprueba la revision desde el estado "En revision".'))
            if r.firma_revisa_id:
                raise UserError(_('Este documento ya fue revisado por %s.') % r.firma_revisa_id.name)
            if r.elabora_id and r.elabora_id.id == self.env.user.id:
                raise UserError(_(
                    'La misma persona no puede elaborar y revisar (PNOGE-001).'))
            today = fields.Date.today()
            r.write({
                'firma_revisa_id': self.env.user.id,
                'fecha_revisa': today,
            })
            # Cerrar la actividad de revisar y abrir la de autorizar
            r.activity_feedback(
                ['mail.mail_activity_data_todo'],
                feedback=_('Revisado por %s') % self.env.user.name)
            r.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('Autorizar documento %s') % r.codigo,
                note=_(
                    '<p>El documento <b>%s</b> (%s v%s) ya fue revisado por %s.</p>'
                    '<p>Por favor revisalo y pulsa <b>"Aprobar y publicar"</b> para hacerlo vigente.</p>'
                ) % (r.name, r.codigo, r.version_actual, self.env.user.name),
                user_id=r.autorizador_id.id,
            )

    def action_aprobar(self):
        for r in self:
            tiene_contenido = r.archivo or (r.contenido_html or '').strip() or \
                              (r.seccion_objetivo or '').strip() or r.actividad_ids
            if not tiene_contenido:
                raise UserError(_(
                    'El documento esta vacio. No se puede autorizar sin contenido.'))
            if r.state != 'en_revision':
                raise UserError(_('Solo se autoriza desde el estado "En revision".'))
            if not r.firma_revisa_id:
                raise UserError(_(
                    'Falta la revision previa. Pidele a %s que abra el documento y pulse '
                    '"Aprobar revision" antes de autorizar.'
                ) % (r.revisor_id.name or 'el revisor asignado'))
            if r.elabora_id and r.elabora_id.id == self.env.user.id:
                raise UserError(_(
                    'El usuario que elaboro el documento (%s) no puede autorizarlo. '
                    'Las firmas de Elabora y Autoriza deben ser personas distintas '
                    '(PNOGE-001 condiciones generales).'
                ) % r.elabora_id.name)
            today = fields.Date.today()
            r.write({
                'state': 'vigente',
                'firma_aprueba_id': self.env.user.id,
                'fecha_aprueba': today,
                'fecha_publicacion': today,
                'fecha_emision': r.fecha_emision or today,
            })
            r.activity_feedback(
                ['mail.mail_activity_data_todo'],
                feedback=_('Autorizado por %s') % self.env.user.name)

    def action_obsoleto(self):
        self.write({'state': 'obsoleto'})

    def action_volver_borrador(self):
        for r in self:
            if r.state == 'vigente':
                raise UserError(_(
                    'No puedes regresar a borrador un documento Vigente. '
                    'Genera nueva version o pasalo a obsoleto.'))
            motivo = (r.motivo_devolucion or '').strip()
            if r.state == 'en_revision' and not motivo:
                raise UserError(_(
                    'Antes de devolver el documento a borrador escribe el motivo en el campo '
                    '"Motivo para devolver". El elaborador lo necesita para corregir.'))
            # Cerrar actividades pendientes de revision/autorizacion
            r.activity_feedback(
                ['mail.mail_activity_data_todo'],
                feedback=_('Devuelto a borrador por %s') % self.env.user.name)
            # Mensaje en el chatter para que quede registro
            if motivo:
                r.message_post(
                    body=_(
                        '<p><b>Documento devuelto a borrador</b> por %s.</p>'
                        '<p><b>Motivo:</b> %s</p>'
                    ) % (self.env.user.name, motivo),
                    subject=_('Devuelto a borrador'),
                )
            # Tarea pendiente para el elaborador (si no es el mismo que devuelve)
            if r.elabora_id and motivo:
                r.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_('Corregir documento %s') % r.codigo,
                    note=_(
                        '<p>El documento <b>%s</b> (%s v%s) fue devuelto a borrador por %s.</p>'
                        '<p><b>Motivo:</b> %s</p>'
                        '<p>Por favor corrige y vuelvelo a mandar a revision.</p>'
                    ) % (r.name, r.codigo, r.version_actual,
                         self.env.user.name, motivo),
                    user_id=r.elabora_id.id,
                )
            # Reset del ciclo de revision para que se firme de nuevo
            r.write({
                'state': 'borrador',
                'motivo_devolucion': False,
                'firma_revisa_id': False,
                'fecha_revisa': False,
            })

    def action_nueva_version(self):
        for r in self:
            if r.state != 'vigente':
                raise UserError(_('Solo puedes generar nueva version desde un documento Vigente.'))
            if not (r.descripcion_cambio_pendiente or '').strip() or \
               not (r.justificacion_pendiente or '').strip():
                raise UserError(_(
                    'Para publicar una nueva version necesitas capturar la descripcion del cambio '
                    'y la justificacion en la pestana "Nueva version".'))
            today = fields.Date.today()
            # Construir snapshot HTML completo con todas las secciones
            def _h(label, html):
                if not (html or '').strip():
                    return ''
                return '<h3>%s</h3>%s' % (label, html)
            secciones_snapshot = ''.join([
                _h('Objetivo', r.seccion_objetivo),
                _h('Alcance', r.seccion_alcance),
                _h('Introduccion', r.seccion_introduccion),
                _h('Mision y Vision', r.seccion_mision_vision),
                _h('Responsabilidades', r.seccion_responsabilidades),
                _h('Organigrama', r.seccion_organigrama),
                _h('Terminos y definiciones', r.seccion_terminos_definiciones),
                _h('Condiciones generales', r.seccion_condiciones_generales),
            ])
            if r.actividad_ids:
                tabla = '<h3>Desarrollo del proceso</h3><table border="1" cellpadding="6" style="border-collapse:collapse;width:100%">'
                tabla += '<thead style="background-color:#e9ecef"><tr><th>#</th><th>Actividad</th><th>Descripcion</th><th>Responsable</th><th>Registro</th></tr></thead><tbody>'
                for a in r.actividad_ids.sorted('sequence'):
                    tabla += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
                        a.sequence or '',
                        a.actividad or '',
                        a.descripcion or '',
                        a.responsable or '',
                        a.registro or '')
                tabla += '</tbody></table>'
                secciones_snapshot += tabla
            secciones_snapshot += ''.join([
                _h('Formatos derivados', r.seccion_formatos_derivados),
                _h('Referencias bibliograficas', r.seccion_referencias),
                _h('Anexos', r.seccion_anexos),
            ])
            snapshot_final = secciones_snapshot or r.contenido_html or ''
            # Archivar version actual como obsoleta
            self.env['amunet.documento.version'].create({
                'documento_id': r.id,
                'version': r.version_actual,
                'fecha': r.fecha_publicacion or today,
                'fecha_emision': r.fecha_emision,
                'fecha_obsolescencia': today,
                'archivo': r.archivo,
                'archivo_filename': r.archivo_filename,
                'contenido_html': snapshot_final,
                'elaboro_id': r.elabora_id.id if r.elabora_id else False,
                'reviso_id': r.firma_revisa_id.id if r.firma_revisa_id else False,
                'aprobado_por_id': r.firma_aprueba_id.id if r.firma_aprueba_id else False,
                'descripcion_cambio': r.descripcion_cambio_pendiente,
                'justificacion': r.justificacion_pendiente,
                'state_historico': 'obsoleto',
            })
            # Incrementar version y resetear ciclo
            try:
                nv = '%02d' % (int(r.version_actual) + 1)
            except (ValueError, TypeError):
                nv = (r.version_actual or '01') + '.1'
            r.write({
                'sustituye_version': r.version_actual,
                'version_actual': nv,
                'state': 'borrador',
                'archivo': False, 'archivo_filename': False,
                'firma_revisa_id': False, 'fecha_revisa': False,
                'firma_aprueba_id': False, 'fecha_aprueba': False,
                'fecha_publicacion': False,
                'fecha_emision': False,
                'descripcion_cambio_pendiente': False,
                'justificacion_pendiente': False,
            })

    @api.model
    def _cron_alertas_vigencia(self):
        """Crea actividades 60/30/0 dias antes de la proxima revision."""
        today = fields.Date.context_today(self)
        for dias in (60, 30, 0):
            fecha_objetivo = today + timedelta(days=dias)
            docs = self.search([
                ('state', '=', 'vigente'),
                ('fecha_vigencia', '=', fecha_objetivo),
            ])
            for d in docs:
                ya_existe = self.env['mail.activity'].search_count([
                    ('res_model', '=', 'amunet.documento'),
                    ('res_id', '=', d.id),
                    ('summary', 'like', 'Documento por revisar: %s' % d.codigo),
                ])
                if ya_existe:
                    continue
                d.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_('Documento por revisar: %s') % d.codigo,
                    note=_(
                        'El documento <b>%s</b> "%s" llega a su fecha de revision en %s dias. '
                        'Inicia el proceso de revision/actualizacion.'
                    ) % (d.codigo, d.name, dias),
                    user_id=d.responsable_id.id or self.env.user.id,
                    date_deadline=d.fecha_vigencia,
                )


class AmunetDocumentoVersion(models.Model):
    _name = 'amunet.documento.version'
    _description = 'Version historica de documento controlado'
    _order = 'fecha desc, id desc'

    documento_id = fields.Many2one('amunet.documento', required=True, ondelete='cascade')
    version = fields.Char(string='Version')
    fecha = fields.Date(string='Fecha de la version')
    fecha_emision = fields.Date(string='Fecha de emision')
    fecha_obsolescencia = fields.Date(string='Fecha en que paso a obsoleto')
    archivo = fields.Binary(string='Archivo Word', attachment=True)
    archivo_filename = fields.Char(string='Nombre de archivo')
    contenido_html = fields.Html(string='Contenido', sanitize=True, sanitize_tags=False)
    descripcion_cambio = fields.Text(string='Descripcion del cambio')
    justificacion = fields.Text(string='Justificacion')
    elaboro_id = fields.Many2one('res.users', string='Elaboro')
    reviso_id = fields.Many2one('res.users', string='Reviso')
    aprobado_por_id = fields.Many2one('res.users', string='Aprobado por')
    state_historico = fields.Selection([
        ('vigente', 'Vigente'),
        ('obsoleto', 'Obsoleto'),
    ], string='Estado historico', default='obsoleto')
    cambios = fields.Text(string='Resumen de cambios')


class AmunetDocumentoDistribucion(models.Model):
    _name = 'amunet.documento.distribucion'
    _description = 'Distribucion de documento controlado'

    documento_id = fields.Many2one('amunet.documento', required=True, ondelete='cascade')
    usuario_id = fields.Many2one('res.users', string='Destinatario', required=True)
    acuse = fields.Boolean(string='Acuse de recibido')
    fecha_acuse = fields.Date(string='Fecha de acuse', readonly=True)

    def action_acusar(self):
        for r in self:
            r.write({'acuse': True, 'fecha_acuse': fields.Date.today()})


class AmunetDocumentoActividad(models.Model):
    _name = 'amunet.documento.actividad'
    _description = 'Actividad del Desarrollo del Proceso (PNOGE-001 Anexo 2)'
    _order = 'sequence, id'

    documento_id = fields.Many2one(
        'amunet.documento', required=True, ondelete='cascade')
    sequence = fields.Integer(string='#', default=10)
    actividad = fields.Char(
        string='Actividad', required=True,
        help='Nombre corto de la actividad (verbo en infinitivo).')
    descripcion = fields.Html(
        string='Descripcion', sanitize=True, sanitize_tags=False,
        help='Detalle paso a paso de lo que se hace, incluyendo notas y referencias a anexos.')
    responsable = fields.Char(
        string='Responsable',
        help='Puesto o rol que ejecuta la actividad. Ej: Elaborador, Documentacion, '
             'Responsable Sanitario.')
    registro = fields.Char(
        string='Registro',
        help='Que se registra o documenta tras la actividad. "No Aplica" si no genera registro.')

    def name_get(self):
        return [(r.id, '%s. %s' % (r.sequence, r.actividad or '')) for r in self]
