# -*- coding: utf-8 -*-
import re
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


AREA_SELECTION = [
    ('GE', 'Generales'),
    ('AD', 'Administracion'),
    ('MA', 'Mantenimiento'),
    ('TV', 'Tecnovigilancia'),
    ('DC', 'Documentacion'),
    ('PR', 'Produccion'),
    ('CC', 'Control de Calidad'),
    ('EST', 'Estabilidad'),
    ('AS', 'Aseguramiento de Calidad'),
    ('AL', 'Almacen'),
    ('IN', 'Ingenieria'),
    ('RH', 'Recursos Humanos'),
    ('OTRO', 'Otra'),
]

CAMPOS_BLOQUEADOS_VIGENTE = (
    'codigo', 'name', 'tipo', 'area', 'version_actual',
    'archivo', 'archivo_filename', 'contenido_html',
    'seccion_objetivo', 'seccion_alcance', 'seccion_introduccion',
    'seccion_mision_vision', 'seccion_responsabilidades',
    'seccion_organigrama', 'seccion_terminos_definiciones',
    'seccion_condiciones_generales', 'seccion_formatos_derivados', 'formato_ids',
    'seccion_referencias', 'seccion_anexos',
    'elabora_id', 'fecha_elabora',
)

CAMPOS_FLUJO_FIRMA = (
    'state', 'firma_revisa_id', 'fecha_revisa', 'firma_aprueba_id',
    'fecha_aprueba', 'fecha_publicacion', 'fecha_emision', 'fecha_vigencia',
)


def _check_documento_child_editable(records, vals=None):
    if records.env.context.get('amunet_documento_workflow_write') or records.env.su:
        return
    docs = records.mapped('documento_id') if records else records.env['amunet.documento']
    if vals and vals.get('documento_id'):
        docs |= records.env['amunet.documento'].browse(vals['documento_id'])
    locked = docs.filtered(lambda d: d.state == 'vigente')
    if locked:
        raise UserError(_(
            'No puedes modificar secciones estructuradas del documento vigente "%s". '
            'Genera una nueva version o pasalo a obsoleto primero.'
        ) % (locked[0].codigo or locked[0].name))


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
    fecha_emision_display = fields.Char(
        string='Fecha de emision (texto)', compute='_compute_fechas_display', store=False)
    fecha_vigencia_display = fields.Char(
        string='Proxima revision (texto)', compute='_compute_fechas_display', store=False)
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

    # Secciones segun PNOGE-001 Anexo 2
    seccion_objetivo = fields.Html(
        string='Objetivo', sanitize=True, sanitize_tags=False)
    seccion_alcance = fields.Html(
        string='Alcance', sanitize=True, sanitize_tags=False)
    seccion_introduccion = fields.Html(
        string='Introduccion', sanitize=True, sanitize_tags=False)
    seccion_mision_vision = fields.Html(
        string='Mision y Vision', sanitize=True, sanitize_tags=False)
    seccion_responsabilidades = fields.Html(
        string='Responsabilidades', sanitize=True, sanitize_tags=False)
    seccion_organigrama = fields.Html(
        string='Organigrama', sanitize=True, sanitize_tags=False)
    seccion_terminos_definiciones = fields.Html(
        string='Terminos y definiciones', sanitize=True, sanitize_tags=False)
    seccion_condiciones_generales = fields.Html(
        string='Condiciones generales', sanitize=True, sanitize_tags=False)
    seccion_formatos_derivados = fields.Html(
        string='Formatos derivados',
        compute='_compute_seccion_formatos_derivados',
        sanitize=False)
    seccion_referencias = fields.Html(
        string='Referencias bibliograficas', sanitize=True, sanitize_tags=False)
    seccion_anexos = fields.Html(
        string='Anexos', sanitize=True, sanitize_tags=False)

    actividad_ids = fields.One2many(
        'amunet.documento.actividad', 'documento_id',
        string='Desarrollo del proceso')

    responsabilidad_ids = fields.One2many(
        'amunet.documento.responsabilidad', 'documento_id',
        string='Responsabilidades por rol')

    termino_ids = fields.One2many(
        'amunet.documento.termino', 'documento_id',
        string='Glosario de terminos')

    # Tres firmas (Elabora / Revisa / Autoriza) + asignaciones previas
    elabora_id = fields.Many2one(
        'res.users', string='Elaboro',
        default=lambda self: self.env.user, tracking=True)
    fecha_elabora = fields.Char(
        string='Fecha elaboracion', tracking=True,
        default=lambda self: fields.Date.context_today(self).strftime('%m/%Y'))
    revisor_id = fields.Many2one(
        'res.users', string='Asignado para revisar', tracking=True)
    autorizador_id = fields.Many2one(
        'res.users', string='Asignado para autorizar', tracking=True)
    firma_revisa_id = fields.Many2one(
        'res.users', string='Firma de revision', readonly=True, tracking=True)
    fecha_revisa = fields.Date(string='Fecha de revision', readonly=True, tracking=True)
    firma_aprueba_id = fields.Many2one(
        'res.users', string='Firma de autorizacion', readonly=True, tracking=True)
    fecha_aprueba = fields.Date(string='Fecha de autorizacion', readonly=True, tracking=True)

    version_ids = fields.One2many(
        'amunet.documento.version', 'documento_id',
        string='Historial de versiones')
    distribucion_ids = fields.One2many(
        'amunet.documento.distribucion', 'documento_id',
        string='Distribucion')
    formato_ids = fields.One2many(
        'amunet.documento.formato', 'documento_id',
        string='Formatos descargables')
    es_supervisor_doc = fields.Boolean(
        compute='_compute_es_supervisor_doc', store=False)
    mi_acuse_pendiente = fields.Boolean(
        compute='_compute_mi_acuse_pendiente', store=False)

    def _compute_es_supervisor_doc(self):
        is_sup = self.env.user.has_group(
            'amunet_documentos.group_supervisor_documentacion')
        for r in self:
            r.es_supervisor_doc = is_sup

    def _compute_mi_acuse_pendiente(self):
        uid = self.env.uid
        for r in self:
            r.mi_acuse_pendiente = (
                r.state == 'vigente'
                and any(d.usuario_id.id == uid and not d.acuse for d in r.distribucion_ids)
            )

    @api.depends('formato_ids', 'formato_ids.codigo', 'formato_ids.nombre',
                 'formato_ids.requiere_aprobacion', 'formato_ids.sequence')
    def _compute_seccion_formatos_derivados(self):
        for r in self:
            if not r.formato_ids:
                r.seccion_formatos_derivados = False
                continue
            filas = ''
            for f in r.formato_ids.sorted('sequence'):
                if f.requiere_aprobacion:
                    badge = (
                        ' <span style="display:inline-block;background:#fef3c7;'
                        'color:#92400e;border-radius:4px;padding:1px 7px;'
                        'font-size:0.78em;font-weight:700;margin-left:6px">'
                        'Solicitar impresión</span>'
                    )
                else:
                    badge = (
                        ' <span style="display:inline-block;background:#f0fdf4;'
                        'color:#166534;border-radius:4px;padding:1px 7px;'
                        'font-size:0.78em;font-weight:700;margin-left:6px">'
                        'Solo lectura</span>'
                    )
                filas += (
                    '<li style="margin-bottom:4px">'
                    '<b>%s</b> — %s%s</li>'
                ) % (f.codigo, f.nombre, badge)
            r.seccion_formatos_derivados = '<ul style="margin:0;padding-left:20px">%s</ul>' % filas

    sugerencia_ids = fields.One2many(
        'amunet.documento.sugerencia', 'documento_id',
        string='Sugerencias de cambio')
    sugerencias_pendientes_count = fields.Integer(
        compute='_compute_sugerencias_pendientes_count', store=False,
        string='Sugerencias pendientes')
    company_id = fields.Many2one(
        'res.company', string='Compania',
        default=lambda self: self.env.company)

    dias_a_vigencia = fields.Integer(
        string='Dias para revision',
        compute='_compute_dias_a_vigencia', store=False)

    # Politica de firmas
    firma_config_id = fields.Many2one(
        'amunet.documento.firma.config',
        compute='_compute_firma_config',
        string='Politica de firmas aplicable', store=True)
    allowed_revisor_ids = fields.Many2many(
        'res.users', 'amunet_doc_allowed_revisor_rel', 'doc_id', 'user_id',
        compute='_compute_allowed_signers', store=False,
        string='Revisores autorizados')
    allowed_autorizador_ids = fields.Many2many(
        'res.users', 'amunet_doc_allowed_autorizador_rel', 'doc_id', 'user_id',
        compute='_compute_allowed_signers', store=False,
        string='Autorizadores autorizados')

    # Firmas snapshot (migracion)
    firmas_snapshot = fields.Text(
        string='Firmas snapshot (migracion)', readonly=True,
        help='Firmas autografas capturadas del documento original al migrar.')

    # Campos transitorios
    descripcion_cambio_pendiente = fields.Text(string='Descripcion del cambio')
    justificacion_pendiente = fields.Text(string='Justificacion del cambio')
    motivo_devolucion = fields.Text(string='Motivo para devolver')

    _codigo_uniq = models.Constraint(
        'unique(codigo)',
        'El codigo del documento debe ser unico.',
    )

    @api.depends('fecha_emision', 'fecha_vigencia')
    def _compute_fechas_display(self):
        MESES = {
            1:'Ene',2:'Feb',3:'Mar',4:'Abr',5:'May',6:'Jun',
            7:'Jul',8:'Ago',9:'Sep',10:'Oct',11:'Nov',12:'Dic',
        }
        for rec in self:
            rec.fecha_emision_display = (
                f"{MESES[rec.fecha_emision.month]} {rec.fecha_emision.year}"
                if rec.fecha_emision else ''
            )
            rec.fecha_vigencia_display = (
                f"{MESES[rec.fecha_vigencia.month]} {rec.fecha_vigencia.year}"
                if rec.fecha_vigencia else ''
            )

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

    @api.depends('area')
    def _compute_firma_config(self):
        Config = self.env['amunet.documento.firma.config']
        for r in self:
            r.firma_config_id = Config._find_for_area(r.area)

    @api.depends('firma_config_id',
                 'firma_config_id.revisor_user_ids',
                 'firma_config_id.autorizador_user_ids')
    def _compute_allowed_signers(self):
        AllUsers = self.env['res.users']
        for r in self:
            if r.firma_config_id and r.firma_config_id.revisor_user_ids:
                r.allowed_revisor_ids = r.firma_config_id.revisor_user_ids
            else:
                r.allowed_revisor_ids = AllUsers.search([('share', '=', False)])
            if r.firma_config_id and r.firma_config_id.autorizador_user_ids:
                r.allowed_autorizador_ids = r.firma_config_id.autorizador_user_ids
            else:
                r.allowed_autorizador_ids = AllUsers.search([('share', '=', False)])

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

    def action_open_sugerencia_wizard(self):
        self.ensure_one()
        return {
            'name': _('Control de cambios: %s') % self.codigo,
            'type': 'ir.actions.act_window',
            'res_model': 'amunet.documento.sugerencia',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_documento_id': self.id},
        }

    @staticmethod
    def _formatear_headers_anexos(html):
        """Convierte párrafos que inician con 'Anexo N' en un bloque visual destacado."""
        if not html or 'Anexo' not in str(html):
            return html
        html_str = str(html)
        STYLE = (
            '<div style="background:#e8f4fd;border-left:4px solid #1565c0;'
            'padding:10px 14px;margin:24px 0 8px 0;border-radius:0 4px 4px 0;">'
            '<strong style="font-size:1.05em;color:#0d47a1;">{}</strong>'
            '</div>'
        )
        def _strip_tags(s):
            return re.sub(r'<[^>]+>', '', s)

        def _repl(m):
            text = _strip_tags(m.group(0)).strip()
            if re.match(r'^Anexo\s+\d+', text, re.IGNORECASE):
                return STYLE.format(text)
            return m.group(0)

        return re.sub(
            r'<p\b[^>]*>.*?</p>',
            _repl,
            html_str,
            flags=re.IGNORECASE | re.DOTALL
        )

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
            if vals.get('seccion_anexos'):
                vals['seccion_anexos'] = self._formatear_headers_anexos(vals['seccion_anexos'])
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('seccion_anexos'):
            vals['seccion_anexos'] = self._formatear_headers_anexos(vals['seccion_anexos'])
        if (
            set(CAMPOS_FLUJO_FIRMA).intersection(vals.keys())
            and not self.env.context.get('amunet_documento_workflow_write')
            and not self.env.su
        ):
            raise UserError(_(
                'Los campos de estado y firma de documentos controlados solo '
                'pueden cambiarse desde las acciones de flujo con firma electronica.'
            ))
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

    def _workflow_write(self, vals):
        return self.with_context(amunet_documento_workflow_write=True).write(vals)

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_aprobar_revision': _('Aprobar revision de documento'),
            '_signature_aprobar': _('Aprobar y publicar documento'),
            '_signature_acuse_lectura': _('Confirmar lectura de documento'),
        }

    def _signature_acuse_lectura(self):
        self.ensure_one()
        uid = self.env.uid
        pendiente = self.distribucion_ids.filtered(
            lambda d: d.usuario_id.id == uid and not d.acuse)
        if pendiente:
            pendiente.with_context(amunet_documento_workflow_write=True).write(
                {'acuse': True, 'fecha_acuse': fields.Date.today()})

    def _open_signature_wizard(self, method_name, signature_type, reason):
        self.ensure_one()
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, method_name, signature_type, reason)

    def action_print_documento(self):
        self.ensure_one()
        return self.env.ref(
            'amunet_documentos.action_report_documento_completo'
        ).report_action(self)

    def _validar_estructura_pnoge_001(self):
        self.ensure_one()
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
            return
        if self.archivo:
            requeridos = [r for r in requeridos
                          if r[0] in ('seccion_objetivo', 'seccion_alcance')]
        faltantes = [label for (f, label) in requeridos if _vacio(getattr(self, f))]
        if self.tipo in ('pno', 'manual', 'instructivo') and not self.actividad_ids and not self.archivo:
            faltantes.append('Desarrollo del proceso (al menos una actividad)')
        actos_vacias = [a for a in self.actividad_ids if not (a.actividad or '').strip()]
        if actos_vacias:
            faltantes.append(
                'Actividades sin número/nombre (%d fila(s) vacías en Desarrollo del proceso)'
                % len(actos_vacias)
            )
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
                    '(Objetivo, Alcance, Desarrollo del proceso, etc.) o adjunta el archivo Word.'))
            if not r.elabora_id:
                raise UserError(_('Asigna quien elaboro el documento antes de mandarlo a revision.'))
            if not r.revisor_id:
                raise UserError(_('Asigna quien debe revisar el documento (campo "Asignado para revisar").'))
            if not r.autorizador_id:
                raise UserError(_('Asigna quien debe autorizar el documento (campo "Asignado para autorizar").'))
            if r.firma_config_id and r.firma_config_id.revisor_user_ids \
                    and r.revisor_id not in r.firma_config_id.revisor_user_ids:
                raise UserError(_(
                    'El revisor %s no esta autorizado para revisar documentos del area "%s" '
                    'segun la politica de firmas "%s".'
                ) % (r.revisor_id.name,
                     dict(r._fields['area'].selection).get(r.area, r.area),
                     r.firma_config_id.name))
            if r.firma_config_id and r.firma_config_id.autorizador_user_ids \
                    and r.autorizador_id not in r.firma_config_id.autorizador_user_ids:
                raise UserError(_(
                    'El autorizador %s no esta autorizado segun la politica de firmas "%s".'
                ) % (r.autorizador_id.name, r.firma_config_id.name))
            r._validar_estructura_pnoge_001()
            r._workflow_write({'state': 'en_revision'})
            r.message_subscribe(partner_ids=[r.revisor_id.partner_id.id,
                                              r.autorizador_id.partner_id.id])
            r.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('Revisar documento %s') % r.codigo,
                note=_(
                    '<p>Revisa el documento <b>%s</b> (%s v%s).</p>'
                    '<p>Si esta correcto, pulsa <b>"Aprobar revision"</b>. '
                    'Si necesita cambios, devuelvelo a borrador con motivo.</p>'
                ) % (r.name, r.codigo, r.version_actual),
                user_id=r.revisor_id.id,
            )

    def action_aprobar_revision(self):
        self.ensure_one()
        self._check_aprobar_revision()
        return self._open_signature_wizard(
            '_signature_aprobar_revision',
            _('Aprobar revision de documento'),
            _('Firma de revision del documento %s version %s.') % (
                self.codigo, self.version_actual),
        )

    def _check_aprobar_revision(self):
        for r in self:
            if r.state != 'en_revision':
                raise UserError(_('Solo se aprueba la revision desde el estado "En revision".'))
            if r.firma_revisa_id:
                raise UserError(_('Este documento ya fue revisado por %s.') % r.firma_revisa_id.name)
            if not r.revisor_id:
                raise UserError(_('Este documento no tiene revisor asignado.'))
            if r.revisor_id != self.env.user:
                raise UserError(_(
                    'Solo el revisor asignado (%s) puede firmar la revision.'
                ) % r.revisor_id.name)
            if r.elabora_id and r.elabora_id.id == self.env.user.id:
                raise UserError(_('La misma persona no puede elaborar y revisar (PNOGE-001).'))

    def _signature_aprobar_revision(self):
        self.ensure_one()
        self._check_aprobar_revision()
        for r in self:
            today = fields.Date.today()
            r._workflow_write({'firma_revisa_id': self.env.user.id, 'fecha_revisa': today})
            r.activity_feedback(
                ['mail.mail_activity_data_todo'],
                feedback=_('Revisado por %s') % self.env.user.name)
            r.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('Autorizar documento %s') % r.codigo,
                note=_(
                    '<p>El documento <b>%s</b> (%s v%s) ya fue revisado por %s.</p>'
                    '<p>Pulsa <b>"Aprobar y publicar"</b> para hacerlo vigente.</p>'
                ) % (r.name, r.codigo, r.version_actual, self.env.user.name),
                user_id=r.autorizador_id.id,
            )

    def action_aprobar(self):
        self.ensure_one()
        self._check_aprobar()
        return self._open_signature_wizard(
            '_signature_aprobar',
            _('Aprobar y publicar documento'),
            _('Firma de autorizacion del documento %s version %s.') % (
                self.codigo, self.version_actual),
        )

    def _check_aprobar(self):
        for r in self:
            tiene_contenido = r.archivo or (r.contenido_html or '').strip() or \
                              (r.seccion_objetivo or '').strip() or r.actividad_ids
            if not tiene_contenido:
                raise UserError(_('El documento esta vacio. No se puede autorizar sin contenido.'))
            if r.state != 'en_revision':
                raise UserError(_('Solo se autoriza desde el estado "En revision".'))
            if not r.firma_revisa_id:
                raise UserError(_(
                    'Falta la revision previa. Pidele a %s que pulse "Aprobar revision" antes.'
                ) % (r.revisor_id.name or 'el revisor asignado'))
            if not r.autorizador_id:
                raise UserError(_('Este documento no tiene autorizador asignado.'))
            if r.autorizador_id != self.env.user:
                raise UserError(_(
                    'Solo el autorizador asignado (%s) puede firmar la autorizacion.'
                ) % r.autorizador_id.name)
            if r.elabora_id and r.elabora_id.id == self.env.user.id:
                raise UserError(_(
                    'El usuario que elaboro el documento (%s) no puede autorizarlo (PNOGE-001).'
                ) % r.elabora_id.name)
            if r.firma_revisa_id and r.firma_revisa_id == self.env.user:
                raise UserError(_('La misma persona no puede revisar y autorizar.'))

    def _signature_aprobar(self):
        self.ensure_one()
        self._check_aprobar()
        for r in self:
            today = fields.Date.today()
            fecha_emision = r.fecha_emision or today
            r._workflow_write({
                'state': 'vigente',
                'firma_aprueba_id': self.env.user.id,
                'fecha_aprueba': today,
                'fecha_publicacion': today,
                'fecha_emision': fecha_emision,
                'fecha_vigencia': fecha_emision + relativedelta(years=2),
            })
            r._auto_distribuir_signatarios(today)
            r.activity_feedback(
                ['mail.mail_activity_data_todo'],
                feedback=_('Autorizado por %s') % self.env.user.name)

    def _auto_distribuir_signatarios(self, today=None):
        """Al publicar, registra acuse automatico para elaboro/reviso/autorizo."""
        today = today or fields.Date.today()
        Dist = self.env['amunet.documento.distribucion']
        for r in self:
            uids = {uid for uid in (
                r.elabora_id.id, r.firma_revisa_id.id, r.firma_aprueba_id.id
            ) if uid}
            existentes = {d.usuario_id.id: d for d in r.distribucion_ids}
            for uid in uids:
                if uid in existentes:
                    if not existentes[uid].acuse:
                        existentes[uid].with_context(
                            amunet_documento_workflow_write=True
                        ).write({'acuse': True, 'fecha_acuse': today})
                else:
                    Dist.create({
                        'documento_id': r.id,
                        'usuario_id': uid,
                        'acuse': True,
                        'fecha_acuse': today,
                    })

    def action_yo_lo_lei(self):
        self.ensure_one()
        return self._open_signature_wizard(
            '_signature_acuse_lectura',
            'Acuse de lectura',
            'Confirmo que he leido y entendido el documento %s v%s' % (
                self.codigo, self.version_actual or ''),
        )

    def action_eliminar_borrador(self):
        for r in self:
            if r.state != 'borrador':
                raise UserError(_('Solo puedes eliminar documentos en estado Borrador.'))
        self.unlink()
        return {'type': 'ir.actions.act_window_close'}

    def action_obsoleto(self):
        self._workflow_write({'state': 'obsoleto'})

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
            r.activity_feedback(
                ['mail.mail_activity_data_todo'],
                feedback=_('Devuelto a borrador por %s') % self.env.user.name)
            if motivo:
                r.message_post(
                    body=_(
                        '<p><b>Documento devuelto a borrador</b> por %s.</p>'
                        '<p><b>Motivo:</b> %s</p>'
                    ) % (self.env.user.name, motivo),
                    subject=_('Devuelto a borrador'),
                )
            if r.elabora_id and motivo:
                r.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_('Corregir documento %s') % r.codigo,
                    note=_(
                        '<p>El documento <b>%s</b> (%s v%s) fue devuelto a borrador por %s.</p>'
                        '<p><b>Motivo:</b> %s</p>'
                        '<p>Corrige y vuelvelo a mandar a revision.</p>'
                    ) % (r.name, r.codigo, r.version_actual,
                         self.env.user.name, motivo),
                    user_id=r.elabora_id.id,
                )
            r._workflow_write({
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
            self.env['amunet.documento.version'].with_context(
                amunet_documento_workflow_write=True).create({
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
            try:
                nv = '%02d' % (int(r.version_actual) + 1)
            except (ValueError, TypeError):
                nv = (r.version_actual or '01') + '.1'
            r._workflow_write({
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
                        'El documento <b>%s</b> "%s" llega a su fecha de revision en %s dias.'
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
    diff_html = fields.Html(string='Cambios vs. versión anterior', compute='_compute_diff_html', sanitize=False)

    def _compute_diff_html(self):
        import re
        from difflib import SequenceMatcher

        def strip_html(html_text):
            if not html_text:
                return ''
            text = re.sub(r'<[^>]+>', ' ', html_text)
            text = re.sub(r'&nbsp;', ' ', text)
            text = re.sub(r'&[a-z]+;', '', text)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()

        for record in self:
            prev = self.env['amunet.documento.version'].search([
                ('documento_id', '=', record.documento_id.id),
                ('fecha', '<', record.fecha),
            ], order='fecha desc', limit=1)

            if not prev:
                record.diff_html = (
                    '<p style="color:#6b7280;font-style:italic">'
                    'Primera versión — sin versión anterior para comparar.</p>'
                )
                continue

            old_words = strip_html(prev.contenido_html).split()
            new_words = strip_html(record.contenido_html).split()
            matcher = SequenceMatcher(None, old_words, new_words, autojunk=False)
            parts = []

            for op, i1, i2, j1, j2 in matcher.get_opcodes():
                if op == 'equal':
                    parts.append(' '.join(new_words[j1:j2]))
                elif op == 'insert':
                    chunk = ' '.join(new_words[j1:j2])
                    parts.append(
                        '<strong style="background:#dcfce7;color:#166534;padding:0 2px">%s</strong>' % chunk
                    )
                elif op == 'delete':
                    chunk = ' '.join(old_words[i1:i2])
                    parts.append(
                        '<del style="background:#fee2e2;color:#991b1b;padding:0 2px">%s</del>' % chunk
                    )
                elif op == 'replace':
                    old_chunk = ' '.join(old_words[i1:i2])
                    new_chunk = ' '.join(new_words[j1:j2])
                    parts.append(
                        '<del style="background:#fee2e2;color:#991b1b;padding:0 2px">%s</del> '
                        '<strong style="background:#dcfce7;color:#166534;padding:0 2px">%s</strong>'
                        % (old_chunk, new_chunk)
                    )

            record.diff_html = '<div style="line-height:2;font-size:0.95em">%s</div>' % ' '.join(parts)

    def _check_version_workflow_write(self):
        if (
            not self.env.context.get('amunet_documento_workflow_write')
            and not self.env.su
        ):
            raise UserError(_(
                'Las versiones historicas de documentos controlados solo '
                'pueden generarse desde el flujo de nueva version.'
            ))

    @api.model_create_multi
    def create(self, vals_list):
        self._check_version_workflow_write()
        return super().create(vals_list)

    def write(self, vals):
        self._check_version_workflow_write()
        return super().write(vals)

    def unlink(self):
        self._check_version_workflow_write()
        return super().unlink()


class AmunetDocumentoDistribucion(models.Model):
    _name = 'amunet.documento.distribucion'
    _description = 'Distribucion de documento controlado'

    documento_id = fields.Many2one('amunet.documento', required=True, ondelete='cascade')
    usuario_id = fields.Many2one('res.users', string='Destinatario', required=True)
    acuse = fields.Boolean(string='Acuse de recibido')
    fecha_acuse = fields.Date(string='Fecha de acuse', readonly=True)

    doc_codigo = fields.Char(related='documento_id.codigo', store=True, string='Codigo')
    doc_name = fields.Char(related='documento_id.name', store=True, string='Documento')
    doc_area = fields.Selection(related='documento_id.area', store=True, string='Area')
    doc_state = fields.Selection(related='documento_id.state', store=True, string='Estado')

    def write(self, vals):
        if ('acuse' in vals or 'fecha_acuse' in vals) \
                and not self.env.context.get('amunet_documento_workflow_write') \
                and not self.env.su:
            raise UserError(_(
                'El acuse de lectura solo puede registrarse mediante firma electronica.'))
        return super().write(vals)

    def action_acusar(self):
        for r in self:
            r.with_context(amunet_documento_workflow_write=True).write(
                {'acuse': True, 'fecha_acuse': fields.Date.today()})

    def _amunet_signature_allowed_methods(self):
        return {'_signature_acuse': _('Confirmar lectura de documento')}

    def _signature_acuse(self):
        self.ensure_one()
        if self.usuario_id.id != self.env.uid:
            raise UserError(_('Solo puedes firmar tu propio acuse.'))
        self.with_context(amunet_documento_workflow_write=True).write(
            {'acuse': True, 'fecha_acuse': fields.Date.today()})

    def action_abrir_documento(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'amunet.documento',
            'res_id': self.documento_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_yo_lo_lei_desde_lista(self):
        self.ensure_one()
        if self.usuario_id.id != self.env.uid:
            raise UserError(_('Solo puedes confirmar tu propio acuse.'))
        return self.env['amunet.generic.signature.wizard'].open_for(
            self,
            '_signature_acuse',
            'Acuse de lectura',
            'Confirmo que he leido y entendido el documento %s v%s' % (
                self.doc_codigo or '', self.documento_id.version_actual or ''),
        )


class AmunetDocumentoActividad(models.Model):
    _name = 'amunet.documento.actividad'
    _description = 'Actividad del Desarrollo del Proceso (PNOGE-001 Anexo 2)'
    _order = 'sequence, id'

    documento_id = fields.Many2one(
        'amunet.documento', required=True, ondelete='cascade')
    sequence = fields.Integer(string='#', default=10)
    actividad = fields.Char(string='Actividad')
    descripcion = fields.Html(string='Descripcion', sanitize=True, sanitize_tags=False)
    responsable = fields.Char(string='Responsable')
    registro = fields.Char(string='Registro')

    def name_get(self):
        return [(r.id, '%s. %s' % (r.sequence, r.actividad or '')) for r in self]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            _check_documento_child_editable(self, vals)
        return super().create(vals_list)

    def write(self, vals):
        _check_documento_child_editable(self, vals)
        return super().write(vals)

    def unlink(self):
        _check_documento_child_editable(self)
        return super().unlink()


class AmunetDocumentoResponsabilidad(models.Model):
    _name = 'amunet.documento.responsabilidad'
    _description = 'Responsabilidad por rol (PNOGE-001)'
    _order = 'sequence, id'

    documento_id = fields.Many2one(
        'amunet.documento', required=True, ondelete='cascade')
    sequence = fields.Integer(string='#', default=10)
    rol = fields.Char(
        string='Rol / Puesto', required=True,
        help='Ej: "Del Responsable Sanitario", "Del area de Documentacion", '
             '"De todo el personal".')
    descripcion = fields.Html(
        string='Responsabilidades',
        sanitize=True, sanitize_tags=False,
        help='Lista de obligaciones de este rol. Usa vinetas para que se vea claro.')

    def name_get(self):
        return [(r.id, r.rol or '') for r in self]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            _check_documento_child_editable(self, vals)
        return super().create(vals_list)

    def write(self, vals):
        _check_documento_child_editable(self, vals)
        return super().write(vals)

    def unlink(self):
        _check_documento_child_editable(self)
        return super().unlink()


class AmunetDocumentoTermino(models.Model):
    _name = 'amunet.documento.termino'
    _description = 'Termino y definicion (PNOGE-001)'
    _order = 'sequence, concepto'

    documento_id = fields.Many2one(
        'amunet.documento', required=True, ondelete='cascade')
    sequence = fields.Integer(string='#', default=10)
    concepto = fields.Char(
        string='Concepto', required=True,
        help='Termino o sigla a definir. Ej: BPD, PNO, Procedimiento.')
    definicion = fields.Html(
        string='Definicion', sanitize=True, sanitize_tags=False,
        help='Explicacion clara del termino o sigla.')

    def name_get(self):
        return [(r.id, r.concepto or '') for r in self]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            _check_documento_child_editable(self, vals)
        return super().create(vals_list)

    def write(self, vals):
        _check_documento_child_editable(self, vals)
        return super().write(vals)

    def unlink(self):
        _check_documento_child_editable(self)
        return super().unlink()
