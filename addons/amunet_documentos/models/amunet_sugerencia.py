# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AmunetSeccionDocumento(models.Model):
    _name = 'amunet.seccion.documento'
    _description = 'Sección de documento controlado (catálogo)'
    _order = 'sequence, name'

    sequence = fields.Integer(default=10)
    name = fields.Char(string='Sección', required=True)


class AmunetSugerenciaLinea(models.Model):
    _name = 'amunet.sugerencia.linea'
    _description = 'Línea de cambio específico en control de cambios'
    _order = 'sequence, id'

    sugerencia_id  = fields.Many2one(
        'amunet.documento.sugerencia', required=True, ondelete='cascade')
    sequence       = fields.Integer(default=10)
    elemento       = fields.Char(string='Elemento que cambia')
    texto_actual   = fields.Text(string='Dice actualmente')
    texto_propuesto = fields.Text(string='Debe decir')


class AmunetSugerenciaComite(models.Model):
    _name = 'amunet.sugerencia.comite'
    _description = 'Integrante del comité técnico en control de cambios'
    _order = 'sequence, id'

    sugerencia_id    = fields.Many2one(
        'amunet.documento.sugerencia', required=True, ondelete='cascade')
    sequence         = fields.Integer(default=10)
    area             = fields.Char(string='Área')
    fecha            = fields.Date(string='Fecha', default=fields.Date.today)
    nombre_id        = fields.Many2one('res.users', string='Nombre')
    usuario_firma_id = fields.Many2one('res.users', string='Firmado por', readonly=True)
    fecha_firma      = fields.Date(string='Fecha de firma', readonly=True)

    @api.onchange('nombre_id')
    def _onchange_nombre_id(self):
        if self.nombre_id:
            try:
                employee = self.env['hr.employee'].search(
                    [('user_id', '=', self.nombre_id.id)], limit=1)
                if employee and employee.department_id:
                    self.area = employee.department_id.name
            except Exception:
                pass

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_firmar_comite': _('Firma de comité técnico'),
        }

    def action_firmar_comite(self):
        self.ensure_one()
        if not self.env.user.has_group('amunet_documentos.group_comite_tecnico'):
            raise UserError(_('Solo los integrantes del comité técnico pueden firmar aquí.'))
        if self.usuario_firma_id:
            raise UserError(_('Este integrante ya firmó el control de cambios.'))
        return self.env['amunet.generic.signature.wizard'].open_for(
            self,
            '_signature_firmar_comite',
            _('Firma de comité técnico'),
            _('Aprobación del control de cambios: %s') % self.sugerencia_id.name,
        )

    def _signature_firmar_comite(self):
        self.ensure_one()
        if not self.env.user.has_group('amunet_documentos.group_comite_tecnico'):
            raise UserError(_('Solo los integrantes del comité técnico pueden firmar aquí.'))
        self.write({
            'usuario_firma_id': self.env.user.id,
            'fecha_firma': fields.Date.today(),
        })
        self.sugerencia_id._message_log(
            body=_('<p><b>%s</b> firmó como integrante del comité técnico (área: %s).</p>')
                 % (self.env.user.name, self.area or ''),
        )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for r in records:
            if r.nombre_id and r.sugerencia_id:
                r.sugerencia_id.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_('Firma requerida — comité técnico'),
                    note=_('<p>Fuiste agregado al comité técnico del control de cambios '
                           '<b>%s</b>. Abre el registro y usa el botón <b>Firmar</b> '
                           'para registrar tu aprobación con PIN.</p>')
                          % r.sugerencia_id.name,
                    user_id=r.nombre_id.id,
                )
        return records


_SECCION_CAMPO_MAP = {
    'Objetivo':                   'seccion_objetivo',
    'Alcance':                    'seccion_alcance',
    'Responsabilidades':          'seccion_responsabilidades',
    'Términos y definiciones':    'seccion_terminos_definiciones',
    'Condiciones generales':      'seccion_condiciones_generales',
    'Desarrollo del proceso':     '_actividades',
    'Formatos derivados':         'seccion_formatos_derivados',
    'Referencias bibliográficas': 'seccion_referencias',
}


class AmunetDocumentoSugerencia(models.Model):
    _name = 'amunet.documento.sugerencia'
    _description = 'Control de cambios en documento controlado'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_creacion desc'

    name = fields.Char(string='Resumen', compute='_compute_name', store=True)
    documento_id = fields.Many2one(
        'amunet.documento', required=True, ondelete='cascade', tracking=True)
    documento_codigo = fields.Char(related='documento_id.codigo',
                                   string='Codigo del documento', store=True)
    secciones_ids = fields.Many2many(
        'amunet.seccion.documento',
        'amunet_sugerencia_seccion_rel',
        'sugerencia_id', 'seccion_id',
        string='Secciones afectadas',
        tracking=True)
    cambios_ids = fields.One2many(
        'amunet.sugerencia.linea', 'sugerencia_id',
        string='Detalle de cambios')
    referencia_html = fields.Html(
        string='Contenido actual del documento',
        compute='_compute_referencia_html',
        sanitize=False)
    diff_html = fields.Html(
        string='Resumen de cambios',
        compute='_compute_diff_html',
        sanitize=False)
    motivo = fields.Text(string='Justificación del cambio', required=True, tracking=True)
    aplica_analisis_riesgos = fields.Boolean(
        string='Aplica análisis de riesgos', default=False, tracking=True)
    numero_analisis_riesgos = fields.Char(
        string='No. de análisis de riesgos', tracking=True)

    tipo_cambio = fields.Selection([
        ('planeado',    'Planeado'),
        ('no_planeado', 'No planeado'),
    ], string='Tipo de cambio', tracking=True)
    numero_desviacion = fields.Char(
        string='No. de desviación / no conformidad', tracking=True)

    # Alcance del cambio
    alcance_material   = fields.Boolean(string='Material')
    alcance_documentos = fields.Boolean(string='Documentos')
    alcance_equipo     = fields.Boolean(string='Equipos')
    alcance_procesos   = fields.Boolean(string='Procesos')
    alcance_estructura = fields.Boolean(string='Infraestructura')
    alcance_sgc        = fields.Boolean(string='SGC')

    adjunto_ids = fields.Many2many(
        'ir.attachment',
        'amunet_sugerencia_adjunto_rel',
        'sugerencia_id', 'attachment_id',
        string='Archivos del cambio',
        help='Adjunta aquí los nuevos formatos u otros archivos relacionados con este cambio.')

    comite_ids = fields.One2many(
        'amunet.sugerencia.comite', 'sugerencia_id', string='Comité técnico')
    comite_users_ids = fields.Many2many(
        'res.users', compute='_compute_comite_users_ids')

    @api.depends('secciones_ids', 'documento_id')
    def _compute_referencia_html(self):
        for r in self:
            if not r.documento_id or not r.secciones_ids:
                r.referencia_html = False
                continue
            columnas = []
            tabla_actividades = ''
            for seccion in r.secciones_ids.sorted('sequence'):
                campo = _SECCION_CAMPO_MAP.get(seccion.name)
                if not campo:
                    continue
                if campo == '_actividades':
                    actividades = r.documento_id.actividad_ids.sorted('sequence')
                    if actividades:
                        filas = ''.join(
                            '<tr>'
                            '<td style="padding:3px 6px;border:1px solid #ddd;white-space:nowrap">%s</td>'
                            '<td style="padding:3px 6px;border:1px solid #ddd">%s</td>'
                            '<td style="padding:3px 6px;border:1px solid #ddd">%s</td>'
                            '<td style="padding:3px 6px;border:1px solid #ddd;white-space:nowrap">%s</td>'
                            '</tr>' % (
                                a.sequence, a.actividad or '',
                                a.descripcion or '', a.responsable or '')
                            for a in actividades
                        )
                        tabla_actividades = (
                            '<div style="margin-top:12px">'
                            '<p style="margin:0 0 4px;font-weight:bold;font-size:0.85em;'
                            'color:#555;text-transform:uppercase;letter-spacing:.5px">'
                            'Desarrollo del proceso</p>'
                            '<table style="border-collapse:collapse;width:100%;font-size:0.85em">'
                            '<tr style="background:#f5f5f5">'
                            '<th style="padding:3px 6px;border:1px solid #ddd">#</th>'
                            '<th style="padding:3px 6px;border:1px solid #ddd">Actividad</th>'
                            '<th style="padding:3px 6px;border:1px solid #ddd">Descripción</th>'
                            '<th style="padding:3px 6px;border:1px solid #ddd">Responsable</th>'
                            '</tr>' + filas + '</table></div>'
                        )
                elif hasattr(r.documento_id, campo):
                    valor = getattr(r.documento_id, campo)
                    if valor:
                        columnas.append(
                            '<div style="border-left:3px solid #1565c0;padding:12px 16px;'
                            'background:#f8faff;border-radius:0 4px 4px 0;min-width:0">'
                            '<p style="margin:0 0 8px;font-weight:bold;font-size:0.85em;'
                            'color:#555;text-transform:uppercase;letter-spacing:.5px">%s</p>'
                            '<div style="font-size:0.92em;line-height:1.6">%s</div>'
                            '</div>' % (seccion.name, valor)
                        )
            partes = []
            if columnas:
                grid = ''.join(
                    '<div>%s</div>' % c for c in columnas)
                partes.append(
                    '<div style="display:grid;grid-template-columns:repeat(auto-fill,'
                    'minmax(480px,1fr));gap:16px;margin-bottom:12px">%s</div>' % grid)
            if tabla_actividades:
                partes.append(tabla_actividades)
            r.referencia_html = ''.join(partes) if partes else False

    @api.depends('cambios_ids', 'cambios_ids.elemento',
                 'cambios_ids.texto_actual', 'cambios_ids.texto_propuesto',
                 'secciones_ids', 'motivo')
    def _compute_diff_html(self):
        for r in self:
            if not r.cambios_ids:
                r.diff_html = False
                continue
            secciones = ', '.join(r.secciones_ids.mapped('name')) if r.secciones_ids else '—'
            filas = ''
            for i, linea in enumerate(r.cambios_ids.sorted('sequence')):
                bg_row = '#fafafa' if i % 2 == 0 else '#ffffff'
                filas += (
                    '<tr style="background:%(bg)s">'
                    # Elemento
                    '<td style="padding:12px 14px;border-bottom:1px solid #e5e7eb;'
                    'vertical-align:top;width:18%%;min-width:120px">'
                    '<span style="display:inline-block;background:#e0e7ff;color:#3730a3;'
                    'border-radius:4px;padding:4px 10px;font-size:0.9em;font-weight:700;'
                    'white-space:nowrap">%(elemento)s</span></td>'
                    # Dice actualmente
                    '<td style="padding:14px 18px;border-bottom:1px solid #e5e7eb;'
                    'border-left:4px solid #fca5a5;background:#fff8f8;'
                    'vertical-align:top;width:41%%">'
                    '<span style="display:block;font-size:0.78em;font-weight:800;'
                    'color:#dc2626;letter-spacing:.6px;margin-bottom:8px;'
                    'text-transform:uppercase">✕ Dice actualmente</span>'
                    '<div style="font-size:1em;line-height:1.6;color:#374151">%(actual)s</div></td>'
                    # Debe decir
                    '<td style="padding:14px 18px;border-bottom:1px solid #e5e7eb;'
                    'border-left:4px solid #86efac;background:#f6fef9;'
                    'vertical-align:top;width:41%%">'
                    '<span style="display:block;font-size:0.78em;font-weight:800;'
                    'color:#16a34a;letter-spacing:.6px;margin-bottom:8px;'
                    'text-transform:uppercase">✓ Debe decir</span>'
                    '<div style="font-size:1em;line-height:1.6;color:#374151">%(propuesto)s</div></td>'
                    '</tr>'
                ) % {
                    'bg': bg_row,
                    'elemento': linea.elemento or '—',
                    'actual': linea.texto_actual or '<em style="color:#9ca3af">Sin texto anterior</em>',
                    'propuesto': linea.texto_propuesto or '<em style="color:#9ca3af">Se elimina</em>',
                }
            r.diff_html = '''
<div style="margin-top:8px;border-radius:8px;overflow:hidden;
    border:1px solid #e5e7eb;box-shadow:0 1px 3px rgba(0,0,0,.06)">
  <div style="background:#f1f5f9;padding:12px 20px;border-bottom:1px solid #e5e7eb">
    <span style="font-size:0.92em;color:#475569">
      <b>Secciones afectadas:</b> %s
    </span><br/>
    <span style="font-size:0.92em;color:#475569">
      <b>Justificación:</b> %s
    </span>
  </div>
  <table style="width:100%%;border-collapse:collapse;font-size:1em">
    <thead>
      <tr style="background:#f8fafc">
        <th style="padding:12px 18px;text-align:left;font-size:0.85em;
            color:#6b7280;font-weight:700;letter-spacing:.4px;
            border-bottom:2px solid #e5e7eb;text-transform:uppercase">Elemento</th>
        <th style="padding:12px 18px;text-align:left;font-size:0.85em;
            color:#dc2626;font-weight:700;letter-spacing:.4px;
            border-bottom:2px solid #fca5a5;background:#fff8f8;
            text-transform:uppercase">✕ Dice actualmente</th>
        <th style="padding:12px 18px;text-align:left;font-size:0.85em;
            color:#16a34a;font-weight:700;letter-spacing:.4px;
            border-bottom:2px solid #86efac;background:#f6fef9;
            text-transform:uppercase">✓ Debe decir</th>
      </tr>
    </thead>
    <tbody>%s</tbody>
  </table>
</div>''' % (secciones, r.motivo or '—', filas)

    def _compute_comite_users_ids(self):
        group = self.env.ref(
            'amunet_documentos.group_comite_tecnico', raise_if_not_found=False)
        if group:
            self.env.cr.execute(
                "SELECT uid FROM res_groups_users_rel WHERE gid = %s", (group.id,))
            user_ids = [row[0] for row in self.env.cr.fetchall()]
            users = self.env['res.users'].browse(user_ids)
        else:
            users = self.env['res.users']
        for r in self:
            r.comite_users_ids = users

    # Firmas de aplicación del cambio
    realizo_id       = fields.Many2one('res.users', string='Realizó')
    firma_realizo_id = fields.Many2one('res.users', string='Firmó (realizó)', readonly=True)
    fecha_realizo    = fields.Date(string='Fecha firma (realizó)', readonly=True)
    reviso_id        = fields.Many2one('res.users', string='Revisó')
    firma_reviso_id  = fields.Many2one('res.users', string='Firmó (revisó)', readonly=True)
    fecha_reviso     = fields.Date(string='Fecha firma (revisó)', readonly=True)
    aprobo_id        = fields.Many2one('res.users', string='Aprobó')
    firma_aprobo_id  = fields.Many2one('res.users', string='Firmó (aprobó)', readonly=True)
    fecha_aprobo     = fields.Date(string='Fecha firma (aprobó)', readonly=True)

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_realizo':  _('Firma quien realizó el cambio'),
            '_signature_reviso':   _('Firma quien revisó el cambio'),
            '_signature_aprobo':   _('Firma quien aprobó la aplicación del cambio'),
        }

    def _abrir_firma(self, method_name, label):
        self.ensure_one()
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, method_name, label,
            _('Control de cambios: %s') % (self.name or ''))

    def action_firmar_realizo(self):
        self.ensure_one()
        if self.firma_realizo_id:
            raise UserError(_('Ya se registró la firma de quien realizó el cambio.'))
        if self.realizo_id and self.realizo_id != self.env.user:
            raise UserError(_('Solo %s puede firmar en este espacio.') % self.realizo_id.name)
        return self._abrir_firma('_signature_realizo', _('Firma quien realizó el cambio'))

    def _signature_realizo(self):
        self.ensure_one()
        self.write({'firma_realizo_id': self.env.user.id, 'fecha_realizo': fields.Date.today()})
        self._message_log(body=_('<p><b>%s</b> registró su firma como quien realizó el cambio.</p>') % self.env.user.name)

    def action_firmar_reviso(self):
        self.ensure_one()
        if self.firma_reviso_id:
            raise UserError(_('Ya se registró la firma de quien revisó el cambio.'))
        if self.reviso_id and self.reviso_id != self.env.user:
            raise UserError(_('Solo %s puede firmar en este espacio.') % self.reviso_id.name)
        return self._abrir_firma('_signature_reviso', _('Firma quien revisó el cambio'))

    def _signature_reviso(self):
        self.ensure_one()
        self.write({'firma_reviso_id': self.env.user.id, 'fecha_reviso': fields.Date.today()})
        self._message_log(body=_('<p><b>%s</b> registró su firma como quien revisó el cambio.</p>') % self.env.user.name)

    def action_firmar_aprobo(self):
        self.ensure_one()
        if self.firma_aprobo_id:
            raise UserError(_('Ya se registró la firma de quien aprobó el cambio.'))
        if self.aprobo_id and self.aprobo_id != self.env.user:
            raise UserError(_('Solo %s puede firmar en este espacio.') % self.aprobo_id.name)
        return self._abrir_firma('_signature_aprobo', _('Firma quien aprobó la aplicación del cambio'))

    def _signature_aprobo(self):
        self.ensure_one()
        self.write({'firma_aprobo_id': self.env.user.id, 'fecha_aprobo': fields.Date.today()})
        self._message_log(body=_('<p><b>%s</b> registró su firma como quien aprobó la aplicación del cambio.</p>') % self.env.user.name)

    state = fields.Selection([
        ('borrador',  'Borrador'),
        ('pendiente', 'Pendiente de decision'),
        ('aceptada',  'Aceptada'),
        ('rechazada', 'Rechazada'),
    ], string='Estado', default='borrador', tracking=True)
    creado_por_id = fields.Many2one(
        'res.users', string='Propuesto por',
        default=lambda self: self.env.user, readonly=True, tracking=True)
    fecha_creacion = fields.Datetime(
        string='Fecha de propuesta', default=fields.Datetime.now, readonly=True)
    decidido_por_id = fields.Many2one(
        'res.users', string='Decidido por', readonly=True, tracking=True)
    fecha_decision = fields.Datetime(string='Fecha de decision', readonly=True)
    motivo_rechazo = fields.Text(string='Motivo del rechazo', tracking=True)

    @api.depends('documento_codigo', 'secciones_ids')
    def _compute_name(self):
        for r in self:
            secciones = ', '.join(r.secciones_ids.mapped('name')) if r.secciones_ids else '?'
            r.name = '%s — %s' % (r.documento_codigo or '?', secciones)

    @api.model_create_multi
    def create(self, vals_list):
        return super().create(vals_list)

    def action_enviar(self):
        for r in self:
            if r.state not in ('borrador', 'rechazada'):
                raise UserError(_('Este control de cambios ya fue enviado.'))
            if not r.documento_id:
                raise UserError(_('Selecciona el documento antes de enviar.'))
            if not r.secciones_ids:
                raise UserError(_('Indica al menos una sección afectada.'))
            if not (r.motivo or '').strip():
                raise UserError(_('Escribe la justificación del cambio.'))
            vals = {'state': 'pendiente'}
            if r.state == 'rechazada':
                vals.update({
                    'motivo_rechazo': False,
                    'decidido_por_id': False,
                    'fecha_decision': False,
                })
            r.write(vals)
            secciones_str = ', '.join(r.secciones_ids.mapped('name')) or '(sin sección)'
            if r.documento_id.elabora_id:
                r.documento_id.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_('Control de cambios en %s') % r.documento_id.codigo,
                    note=_(
                        '<p>%s envió un control de cambios en <b>%s</b>.</p>'
                        '<p><b>Secciones:</b> %s</p>'
                        '<p><b>Justificación:</b> %s</p>'
                    ) % (r.creado_por_id.name, r.documento_id.codigo,
                         secciones_str, r.motivo),
                    user_id=r.documento_id.elabora_id.id,
                )
            r.documento_id.message_post(
                body=_(
                    '<p><b>Control de cambios enviado</b> por %s.</p>'
                    '<p><b>Secciones:</b> %s — <b>Justificación:</b> %s</p>'
                ) % (r.creado_por_id.name, secciones_str, r.motivo),
                subject=_('Control de cambios'),
            )

    def action_descartar(self):
        for r in self:
            if r.state != 'borrador':
                raise UserError(_('Solo puedes descartar un control de cambios en borrador.'))
        return self.unlink()

    def action_aceptar(self):
        for r in self:
            if r.state != 'pendiente':
                raise UserError(_('Este control de cambios ya tiene decisión (%s).') % r.state)
            if not self.env.user.has_group('amunet_documentos.group_responsable_sanitario'):
                raise UserError(_(
                    'Solo el Responsable Sanitario puede aceptar un control de cambios.'))
            # Validar firmas del comité
            sin_firma = r.comite_ids.filtered(lambda c: not c.usuario_firma_id)
            if r.comite_ids and sin_firma:
                faltantes = ', '.join(sin_firma.mapped('nombre_id.name'))
                raise UserError(_(
                    'Faltan firmas del comité técnico: %s') % faltantes)
            # Validar firmas de aplicación
            falta = []
            if r.realizo_id and not r.firma_realizo_id:
                falta.append(_('Realizó (%s)') % r.realizo_id.name)
            if r.reviso_id and not r.firma_reviso_id:
                falta.append(_('Revisó (%s)') % r.reviso_id.name)
            if r.aprobo_id and not r.firma_aprobo_id:
                falta.append(_('Aprobó (%s)') % r.aprobo_id.name)
            if falta:
                raise UserError(_(
                    'Faltan las siguientes firmas de aplicación:\n%s') % '\n'.join(falta))
            r.write({
                'state': 'aceptada',
                'decidido_por_id': self.env.user.id,
                'fecha_decision': fields.Datetime.now(),
            })
            # Construir descripción en texto plano para el campo Text del documento
            lineas_desc = []
            if r.secciones_ids:
                secs = ', '.join(r.secciones_ids.mapped('name'))
                lineas_desc.append('Secciones afectadas: %s' % secs)
            if r.cambios_ids:
                lineas_desc.append('')
                for linea in r.cambios_ids.sorted('sequence'):
                    lineas_desc.append('• Elemento: %s' % (linea.elemento or '—'))
                    if linea.texto_actual:
                        lineas_desc.append('  Dice actualmente: %s' % linea.texto_actual)
                    if linea.texto_propuesto:
                        lineas_desc.append('  Debe decir: %s' % linea.texto_propuesto)
                    lineas_desc.append('')
            desc_cambio = '\n'.join(lineas_desc).strip() or 'Ver control de cambios adjunto.'
            justificacion = r.motivo or ''
            # Poblar campos del documento y lanzar nueva versión automáticamente
            # Correo directo a la creadora en el propio CC
            r.message_post(
                body=_(
                    '<p>✅ <b>Tu control de cambios fue aprobado</b> por %s.</p>'
                    '<p><b>Documento:</b> %s</p>'
                    '<p>El documento ya quedó en borrador para que apliques los cambios '
                    'y lo mandes a revisión.</p>'
                ) % (self.env.user.name, r.documento_id.codigo),
                subject=_('✅ Control de cambios aprobado — %s') % r.documento_id.codigo,
                subtype_xmlid='mail.mt_comment',
            )
            if r.documento_id and r.documento_id.state == 'vigente':
                r.documento_id.with_context(
                    amunet_documento_workflow_write=True
                ).write({
                    'descripcion_cambio_pendiente': desc_cambio,
                    'justificacion_pendiente': justificacion,
                })
                r.documento_id.action_nueva_version()
                r.documento_id.message_post(
                    body=_(
                        '<p><b>Nueva versión iniciada</b> a partir del control de cambios '
                        'aceptado por %s.</p>'
                    ) % self.env.user.name,
                )
                if r.creado_por_id:
                    r.documento_id.activity_schedule(
                        'mail.mail_activity_data_todo',
                        summary=_('Aplicar cambios en %s y mandar a revisión') % r.documento_id.codigo,
                        note=_(
                            '<p>El control de cambios fue aceptado por %s. '
                            'El documento ya quedó en borrador (nueva versión). '
                            'Aplica los cambios indicados en el contenido y mándalo a revisión.</p>'
                        ) % self.env.user.name,
                        user_id=r.creado_por_id.id,
                    )
            else:
                r.documento_id.message_post(
                    body=_('<p><b>Control de cambios aceptado</b> por %s.</p>') % self.env.user.name,
                )

    def action_rechazar(self):
        for r in self:
            if r.state != 'pendiente':
                raise UserError(_('Este control de cambios ya tiene decisión (%s).') % r.state)
            if not self.env.user.has_group('amunet_documentos.group_responsable_sanitario'):
                raise UserError(_(
                    'Solo el Responsable Sanitario puede rechazar un control de cambios.'))
            if not (r.motivo_rechazo or '').strip():
                raise UserError(_('Indica el motivo del rechazo.'))
            r.write({
                'state': 'rechazada',
                'decidido_por_id': self.env.user.id,
                'fecha_decision': fields.Datetime.now(),
            })
            # Correo directo a la creadora en el propio CC
            r.message_post(
                body=_(
                    '<p>❌ <b>Tu control de cambios fue rechazado</b> por %s.</p>'
                    '<p><b>Documento:</b> %s</p>'
                    '<p><b>Motivo del rechazo:</b> %s</p>'
                    '<p>Puedes corregirlo y volver a enviarlo desde '
                    '"Mis controles de cambio".</p>'
                ) % (self.env.user.name, r.documento_id.codigo, r.motivo_rechazo),
                subject=_('❌ Control de cambios rechazado — %s') % r.documento_id.codigo,
                subtype_xmlid='mail.mt_comment',
            )
            if r.creado_por_id:
                r.documento_id.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_('Control de cambios rechazado en %s') % r.documento_id.codigo,
                    note=_(
                        '<p>%s rechazó el control de cambios.</p><p><b>Motivo:</b> %s</p>'
                    ) % (self.env.user.name, r.motivo_rechazo),
                    user_id=r.creado_por_id.id,
                )
            r.documento_id.message_post(
                body=_(
                    '<p><b>Control de cambios rechazado</b> por %s. <b>Motivo:</b> %s</p>'
                ) % (self.env.user.name, r.motivo_rechazo),
            )
