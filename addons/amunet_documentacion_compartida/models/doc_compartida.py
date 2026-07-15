from datetime import timedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

_CAMPOS_REV = ['rev_materiales', 'rev_volumenes', 'rev_tiempos', 'rev_adicional']

# Grupos (reemplazan los UIDs hardcodeados JORGE_UID/diana_uid).
#  - Validación: programa la fecha y ejecuta los cambios.
#  - Calidad (Supervisor QC o Responsable Sanitario): revisa, aprueba y FIRMA.
G_VALIDACION = 'amunet_documentacion_compartida.group_doc_validacion'
G_CAL_SUP = 'amunet_quality.group_quality_supervisor'
G_CAL_RS = 'amunet_quality.group_quality_sanitary'
G_CAL_ANALISTA = 'amunet_quality.group_quality_user'

# UIDs fijos para el correo de aprobación (Diana, Stacey, Jorge)
_UID_APROBACION = [64, 69, 70]


class DocCompartida(models.Model):
    _name = 'amunet.doc.compartida'
    _description = 'Documentación Compartida'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ── Manual ───────────────────────────────────────────────
    name = fields.Char(string='Manual', required=True, tracking=True)
    carpeta_id = fields.Many2one('amunet.doc.carpeta', string='Carpeta', tracking=True)
    manual_file = fields.Binary(string='Archivo PDF', attachment=True)
    manual_filename = fields.Char(string='Nombre del archivo')

    # ── Fecha programada (solo Jorge) ────────────────────────
    fecha_programada = fields.Date(string='Fecha programada', tracking=True)

    # ── Revisión Calidad ─────────────────────────────────────
    rev_materiales = fields.Selection(
        [('ok', '✓ Correcto'), ('fail', '✗ Incorrecto')],
        string='Precauciones', tracking=True)
    rev_volumenes = fields.Selection(
        [('ok', '✓ Correcto'), ('fail', '✗ Incorrecto')],
        string='Volúmenes de reactivos', tracking=True)
    rev_tiempos = fields.Selection(
        [('ok', '✓ Correcto'), ('fail', '✗ Incorrecto')],
        string='Tiempos de interpretación', tracking=True)
    rev_adicional = fields.Selection(
        [('ok', '✓ Correcto'), ('fail', '✗ Incorrecto')],
        string='Adicional', tracking=True)

    # ── Observaciones / Estatus ──────────────────────────────
    obs_requeridas = fields.Boolean(compute='_compute_estado', store=True)
    observaciones = fields.Text(string='Observaciones', tracking=True)
    # Estado ya NO se auto-aprueba con marcar criterios. Al completar los 4
    # criterios en '✓ Correcto' pasa a 'por_aprobar'; la APROBACIÓN final la
    # da Calidad con FIRMA (PIN) via action_aprobar_firmar.
    state = fields.Selection(
        [('pendiente', 'PENDIENTE'),
         ('por_aprobar', 'LISTO PARA APROBAR'),
         ('aprobado', 'APROBADO')],
        string='Estatus', default='pendiente', tracking=True, copy=False)
    # Revisión completa = los 4 criterios en 'ok' (aún sin firmar).
    revision_completa = fields.Boolean(
        compute='_compute_estado', store=True,
        string='Revisión completa')
    # ── Firma de aprobación (ISO 13485 / CFR 21 Part 11) ─────
    firmante_id = fields.Many2one(
        'res.users', string='Aprobado y firmado por', readonly=True, copy=False)
    fecha_firma = fields.Datetime(
        string='Fecha de firma', readonly=True, copy=False)

    # ── Cerrojo de revisión ──────────────────────────────────
    revisor_activo_id = fields.Many2one(
        'res.users', string='En revisión por', tracking=True)

    # ── Registro del revisor final ───────────────────────────
    revisado_por_id = fields.Many2one('res.users', string='Revisor', readonly=True)
    fecha_revision = fields.Datetime(string='Fecha de revisión', readonly=True)
    revisado_display = fields.Char(
        string='Revisado por', compute='_compute_revisado_display', store=False)

    # ── Historial de revisiones ──────────────────────────────
    historial_ids = fields.One2many(
        'amunet.doc.revision.historial', 'doc_id', string='Historial')
    historial_count = fields.Integer(
        compute='_compute_historial_count', string='Revisiones')

    # ── Computed contextuales (varían por usuario) ───────────
    es_responsable = fields.Boolean(compute='_compute_ctx_usuario')
    es_calidad = fields.Boolean(compute='_compute_ctx_usuario')
    soy_revisor_activo = fields.Boolean(compute='_compute_ctx_usuario')

    # ── Revisión cerrada (todas las columnas llenas y sin revisor activo) ──
    revision_cerrada = fields.Boolean(
        compute='_compute_revision_cerrada', store=False)

    # ────────────────────────────────────────────────────────────────
    # Computes
    # ────────────────────────────────────────────────────────────────

    @api.depends('rev_materiales', 'rev_volumenes', 'rev_tiempos', 'rev_adicional', 'revisor_activo_id')
    def _compute_revision_cerrada(self):
        for rec in self:
            todos_llenos = all(getattr(rec, f) for f in _CAMPOS_REV)
            rec.revision_cerrada = todos_llenos and not rec.revisor_activo_id

    @api.depends('historial_ids')
    def _compute_historial_count(self):
        for rec in self:
            rec.historial_count = len(rec.historial_ids)

    @api.depends('revisor_activo_id')
    @api.depends_context('uid')
    def _compute_ctx_usuario(self):
        uid = self.env.user.id
        es_val = self.env.user.has_group(G_VALIDACION)
        es_cal = self._es_calidad()
        for rec in self:
            rec.es_responsable = es_val
            rec.es_calidad = es_cal
            rec.soy_revisor_activo = bool(rec.revisor_activo_id) and rec.revisor_activo_id.id == uid

    # ── Helpers de rol ───────────────────────────────────────
    def _es_validacion(self):
        return self.env.user.has_group(G_VALIDACION)

    def _es_calidad(self):
        u = self.env.user
        return u.has_group(G_CAL_SUP) or u.has_group(G_CAL_ANALISTA)

    def _usuarios_calidad(self):
        """Usuarios activos de Calidad: Supervisor QC y Analistas QC."""
        users = self.env['res.users']
        for xml_id in (G_CAL_SUP, G_CAL_ANALISTA):
            g = self.env.ref(xml_id, raise_if_not_found=False)
            if g:
                users |= g.sudo().user_ids
        return users.filtered(lambda u: u.active and u.id != 1)

    def _usuarios_validacion(self):
        g = self.env.ref(G_VALIDACION, raise_if_not_found=False)
        if not g:
            return self.env['res.users']
        return g.sudo().user_ids.filtered(lambda u: u.active and u.id != 1)

    @api.depends('revisado_por_id', 'fecha_revision')
    def _compute_revisado_display(self):
        for rec in self:
            if rec.revisado_por_id and rec.fecha_revision:
                fecha = fields.Datetime.context_timestamp(
                    rec, rec.fecha_revision).strftime('%d/%m/%Y %H:%M')
                rec.revisado_display = f"{rec.revisado_por_id.name} · {fecha}"
            else:
                rec.revisado_display = ''

    @api.depends('rev_materiales', 'rev_volumenes', 'rev_tiempos', 'rev_adicional')
    def _compute_estado(self):
        for rec in self:
            reviews = [rec.rev_materiales, rec.rev_volumenes, rec.rev_tiempos, rec.rev_adicional]
            rec.revision_completa = all(r == 'ok' for r in reviews)
            rec.obs_requeridas = any(r == 'fail' for r in reviews)

    # ────────────────────────────────────────────────────────────────
    # Constrains
    # ────────────────────────────────────────────────────────────────

    @api.constrains('manual_filename')
    def _check_formato_pdf(self):
        for rec in self:
            if rec.manual_filename and not rec.manual_filename.lower().endswith('.pdf'):
                raise ValidationError(
                    f'Solo se aceptan archivos PDF. '
                    f'El archivo "{rec.manual_filename}" no es válido.'
                )

    # ────────────────────────────────────────────────────────────────
    # Write override — control de acceso
    # ────────────────────────────────────────────────────────────────

    def write(self, vals):
        uid = self.env.user.id
        campos_revision = {'rev_materiales', 'rev_volumenes', 'rev_tiempos', 'rev_adicional'}
        criterios_cambiados = campos_revision & set(vals)
        bypass = self.env.context.get('bypass_revisor_check')

        # Solo Validación puede cambiar la fecha programada
        if 'fecha_programada' in vals and not bypass and not self._es_validacion():
            raise UserError(
                'Solo el responsable de Validación puede modificar la fecha programada.')

        # Solo Calidad (Supervisor QC / Responsable Sanitario) puede marcar
        # los criterios de revisión. Y no se pueden cambiar si ya está APROBADO
        # y firmado (hay que reabrir primero).
        if criterios_cambiados and not bypass:
            if not self._es_calidad():
                raise UserError(
                    'Solo Calidad puede marcar los criterios de revisión.')
            if any(rec.state == 'aprobado' for rec in self):
                raise UserError(
                    'El manual ya está APROBADO y firmado. Reabre la revisión '
                    'antes de modificar los criterios.')
            # Auto-registramos quién revisó y cuándo.
            vals['revisor_activo_id'] = uid
            vals['revisado_por_id'] = uid
            vals['fecha_revision'] = fields.Datetime.now()

        # Capturar valores de criterios antes de escribir
        valores_antes = {}
        if criterios_cambiados:
            valores_antes = {
                rec.id: {c: getattr(rec, c) for c in criterios_cambiados}
                for rec in self
            }

        result = super().write(vals)

        # Sincronizar observaciones según resultado final
        if criterios_cambiados and 'observaciones' not in vals:
            for rec in self:
                if rec.revision_completa and rec.observaciones != 'Ninguna':
                    rec._write({'observaciones': 'Ninguna'})
                elif rec.obs_requeridas and rec.observaciones == 'Ninguna':
                    rec._write({'observaciones': False})

        # Transición de estado + historial + aviso a Calidad para FIRMAR
        if criterios_cambiados:
            for rec in self:
                for campo in criterios_cambiados:
                    antes = valores_antes[rec.id][campo]
                    despues = getattr(rec, campo)
                    if antes != despues:
                        self.env['amunet.doc.revision.historial'].sudo().create({
                            'doc_id': rec.id,
                            'usuario_id': self.env.user.id,
                            'accion': 'cambio_criterio',
                            'campo': campo,
                            'valor_anterior': antes or False,
                            'valor_nuevo': despues or False,
                            'motivo': vals.get('observaciones') if despues == 'fail' else False,
                        })
                # Estado: la revisión completa deja el manual LISTO PARA APROBAR
                # (la aprobación real la da la firma). Si deja de estar completa,
                # regresa a PENDIENTE.
                if rec.state != 'aprobado':
                    nuevo = 'por_aprobar' if rec.revision_completa else 'pendiente'
                    if rec.state != nuevo:
                        rec._write({'state': nuevo})
                        if nuevo == 'por_aprobar':
                            self.env['amunet.doc.revision.historial'].sudo().create({
                                'doc_id': rec.id,
                                'usuario_id': self.env.user.id,
                                'accion': 'cierre',
                            })
                            rec._notificar_calidad_por_aprobar()

        # Notificar a Calidad cuando se programa una fecha
        if 'fecha_programada' in vals and vals.get('fecha_programada'):
            for rec in self:
                rec._notificar_revision_programada()

        return result

    # ────────────────────────────────────────────────────────────────
    # Aprobación con FIRMA (PIN) — ISO 13485 / CFR 21 Part 11
    # ────────────────────────────────────────────────────────────────

    def _validate_pin(self, password):
        """Reusa el validador de firma de Calidad (PIN o contraseña del usuario)."""
        sig = self.env['amunet.quality.signature.wizard'].new({
            'password': password, 'signature_type': 'authorized'})
        return sig._validate_credentials(password)

    def action_abrir_firma(self):
        """Abre el wizard de firma para aprobar el manual."""
        self.ensure_one()
        if self.state == 'aprobado':
            raise UserError('Este manual ya fue aprobado y firmado.')
        if not self.revision_completa:
            raise UserError('Faltan criterios de revisión por marcar como "✓ Correcto".')
        if not self._es_calidad():
            raise UserError('Solo Calidad (Supervisor QC o Responsable Sanitario) puede firmar.')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Aprobar y firmar',
            'res_model': 'amunet.doc.firma.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_doc_id': self.id},
        }

    def action_aprobar_firmar(self, password):
        """Aprueba el manual con firma electrónica (PIN). Solo Calidad."""
        self.ensure_one()
        if self.state == 'aprobado':
            raise UserError('Este manual ya fue aprobado y firmado.')
        if not self.revision_completa:
            raise UserError('Faltan criterios por marcar como "✓ Correcto".')
        if not self._es_calidad():
            raise UserError('Solo Calidad (Supervisor QC o Responsable Sanitario) puede firmar.')
        if not self._validate_pin(password):
            raise UserError('PIN o contraseña incorrectos.')
        self.with_context(bypass_revisor_check=True).write({
            'state': 'aprobado',
            'firmante_id': self.env.user.id,
            'fecha_firma': fields.Datetime.now(),
            'revisor_activo_id': False,
        })
        self.env['amunet.doc.revision.historial'].sudo().create({
            'doc_id': self.id,
            'usuario_id': self.env.user.id,
            'accion': 'firma',
        })
        self.message_post(
            body='✍️ Manual <b>APROBADO y FIRMADO</b> por <b>%s</b>.' % self.env.user.name,
            message_type='notification', subtype_xmlid='mail.mt_note')
        self._notificar_actualizar_en_sistema()
        return True

    # ────────────────────────────────────────────────────────────────
    # Acciones de botón
    # ────────────────────────────────────────────────────────────────

    def _open_revision_wizard(self, campo, label):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': label,
            'res_model': 'amunet.doc.revision.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_doc_id': self.id,
                'default_campo': campo,
                'default_valor_actual': getattr(self, campo),
                'default_nuevo_valor': getattr(self, campo) or 'ok',
            },
        }

    def action_marcar_materiales(self):
        return self._open_revision_wizard('rev_materiales', 'Materiales')

    def action_marcar_volumenes(self):
        return self._open_revision_wizard('rev_volumenes', 'Volúmenes de reactivos')

    def action_marcar_tiempos(self):
        return self._open_revision_wizard('rev_tiempos', 'Tiempos de interpretación')

    def action_marcar_adicional(self):
        return self._open_revision_wizard('rev_adicional', 'Adicional')

    def action_ver_historial(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Historial — {self.name}',
            'res_model': 'amunet.doc.revision.historial',
            'view_mode': 'list',
            'views': [(False, 'list')],
            'domain': [('doc_id', '=', self.id),
                       ('accion', 'in', ['cierre', 'reapertura'])],
            'target': 'new',
        }

    def action_ver_registro_cambios(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Registro de cambios — {self.name}',
            'res_model': 'amunet.doc.revision.historial',
            'view_mode': 'list',
            'views': [
                (self.env.ref(
                    'amunet_documentacion_compartida.view_doc_criterio_log_list'
                ).id, 'list')
            ],
            'domain': [('doc_id', '=', self.id),
                       ('accion', '=', 'cambio_criterio')],
            'target': 'new',
        }

    def action_reabrir_revision(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reabrir revisión',
            'res_model': 'amunet.doc.reopen.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_doc_id': self.id},
        }

    def action_reemplazar_pdf(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reemplazar PDF',
            'res_model': 'amunet.doc.reemplazo.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_doc_id': self.id},
        }

    def action_eliminar_manual(self):
        if not self._es_validacion():
            from odoo.exceptions import UserError
            raise UserError('Solo el responsable de Validación puede eliminar manuales.')
        return self.unlink()

    def action_tomar_revision(self):
        self.ensure_one()
        if self.state == 'aprobado':
            raise UserError('Este manual ya fue aprobado.')
        uid = self.env.user.id
        # Si otro usuario tiene el cerrojo, pedir confirmación
        if self.revisor_activo_id and self.revisor_activo_id.id != uid:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Tomar revisión',
                'res_model': 'amunet.doc.tomar.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_doc_id': self.id},
            }
        self.revisor_activo_id = uid

    def action_actualizar_en_sistema(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Manual aprobado',
            'res_model': 'amunet.doc.actualizar.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_doc_id': self.id},
        }

    # ────────────────────────────────────────────────────────────────
    # Notificaciones
    # ────────────────────────────────────────────────────────────────

    def _enviar_correo(self, usuarios, asunto, cuerpo_html):
        """Envía correo electrónico directo a una lista de usuarios."""
        destinatarios = usuarios.filtered(lambda u: u.active and u.email)
        if not destinatarios:
            return
        self.env['mail.mail'].sudo().create({
            'subject': asunto,
            'body_html': cuerpo_html,
            'email_from': self.env.company.email or 'odoobot@amunet.com.mx',
            'recipient_ids': [(4, u.partner_id.id) for u in destinatarios],
            'auto_delete': True,
        }).send()

    def _notificar_calidad_por_aprobar(self):
        """Revisión completa: avisar a Calidad (solo actividad Odoo) para que aprueben y firmen."""
        self.ensure_one()
        calidad = self._usuarios_calidad()
        for user in calidad:
            ya = self.activity_ids.filtered(
                lambda a: a.user_id.id == user.id and 'firmar' in (a.summary or '').lower())
            if ya:
                continue
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=fields.Date.today(),
                summary=f'Aprobar y firmar: {self.name}',
                note=f'La revisión del manual <b>{self.name}</b> está completa con todos '
                     f'los criterios en ✓ Correcto.<br/>'
                     f'Entra al manual y pulsa <b>"Aprobar y firmar"</b> (requiere tu PIN).',
                user_id=user.id,
            )

    def _notificar_actualizar_en_sistema(self):
        """Tras la firma: actividad Odoo a todos + correo solo a Diana, Stacey y Jorge."""
        self.ensure_one()
        firmante = self.env.user.name
        todos = (self._usuarios_calidad() | self._usuarios_validacion()).filtered(
            lambda u: u.active and u.id != 1)
        for user in todos:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=fields.Date.today(),
                summary=f'Manual aprobado: {self.name}',
                note=f'El manual <b>{self.name}</b> fue <b>APROBADO y FIRMADO</b> por '
                     f'<b>{firmante}</b>.<br/>'
                     f'(Diana: entra al manual y pulsa <b>"Actualizar en sistema"</b> '
                     f'para subir la versión definitiva a la carpeta LFIA.)',
                user_id=user.id,
            )
        # Correo solo a Diana (64), Stacey (69) y Jorge (70)
        destinatarios_correo = self.env['res.users'].sudo().browse(_UID_APROBACION).filtered(
            lambda u: u.active and u.email)
        self._enviar_correo(
            destinatarios_correo,
            f'✍️ Manual aprobado y firmado: {self.name}',
            f'<p>El manual <b>{self.name}</b> fue <b>APROBADO y FIRMADO</b> por '
            f'<b>{firmante}</b>.</p>'
            f'<p><b>Diana:</b> entra a Odoo → Documentación Técnica → <b>{self.name}</b> '
            f'y pulsa "Actualizar en sistema" para archivar la versión definitiva en la '
            f'carpeta LFIA de Nextcloud.</p>',
        )

    # ────────────────────────────────────────────────────────────────
    # Cron: auto-cierre y recordatorio de revisión
    # ────────────────────────────────────────────────────────────────

    def _cron_check_revisiones(self):
        now = fields.Datetime.now()
        threshold_1min = now - timedelta(seconds=60)
        threshold_5min = now - timedelta(minutes=5)

        # ── Auto-cierre: 4 columnas llenas + 1 min sin actividad ──
        cierre = self.search([
            ('revisor_activo_id', '!=', False),
            ('write_date', '<=', threshold_1min),
            ('rev_materiales', '!=', False),
            ('rev_volumenes', '!=', False),
            ('rev_tiempos', '!=', False),
            ('rev_adicional', '!=', False),
        ])
        for rec in cierre:
            revisor_nombre = rec.revisor_activo_id.name
            rec.with_context(bypass_revisor_check=True).write({'revisor_activo_id': False})
            rec.message_post(
                body=f'✅ Revisión cerrada automáticamente por <b>{revisor_nombre}</b> '
                     f'(todas las columnas completadas, sin cambios por 1 minuto).',
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )

            if rec.revision_completa:
                # Todos ✓ → avisar a Calidad para que aprueben
                rec._notificar_calidad_por_aprobar()
            else:
                # Hay ✗ → avisar a Validación para que corrija el manual
                validacion = rec._usuarios_validacion()
                observ = rec.observaciones or 'Ver observaciones en el manual.'
                for val_user in validacion:
                    ya = rec.activity_ids.filtered(
                        lambda a: a.user_id.id == val_user.id
                        and 'Corregir' in (a.summary or '')
                    )
                    if ya:
                        continue
                    rec.activity_schedule(
                        'mail.mail_activity_data_todo',
                        date_deadline=fields.Date.today(),
                        summary=f'Corregir manual: {rec.name}',
                        note=f'<b>{revisor_nombre}</b> completó la revisión de '
                             f'<b>{rec.name}</b> con criterios en ✗ Incorrecto.<br/>'
                             f'Observación: {observ}<br/>'
                             f'Corrige el manual, recarga el PDF y programa nueva revisión.',
                        user_id=val_user.id,
                    )

        # ── Recordatorio: revisión parcial + 5 min sin actividad ──
        parciales = self.search([
            ('revisor_activo_id', '!=', False),
            ('write_date', '<=', threshold_5min),
        ]).filtered(
            lambda r: any(getattr(r, f) for f in _CAMPOS_REV)
            and not all(getattr(r, f) for f in _CAMPOS_REV)
        )
        for rec in parciales:
            ya_tiene = rec.activity_ids.filtered(
                lambda a: a.user_id == rec.revisor_activo_id
                and 'Finalizar' in (a.summary or '')
            )
            if ya_tiene:
                continue
            rec.activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=fields.Date.today(),
                summary=f'Finalizar revisión: {rec.name}',
                note=f'Iniciaste la revisión del manual <b>{rec.name}</b> '
                     f'pero quedan columnas sin completar. '
                     f'Por favor, termina la revisión o libérala.',
                user_id=rec.revisor_activo_id.id,
            )

    def _notificar_recarga_pdf(self):
        """PDF reemplazado: avisar a toda Calidad (solo actividad Odoo)."""
        self.ensure_one()
        calidad = self._usuarios_calidad()
        cuerpo = (
            f'🔄 El PDF de <b>{self.name}</b> fue actualizado por '
            f'<b>{self.env.user.name}</b>. '
            f'Por favor revisen si los criterios siguen siendo válidos con la nueva versión.'
        )
        self.message_post(
            body=cuerpo,
            partner_ids=calidad.mapped('partner_id').ids,
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
        )
        fecha_str = self.fecha_programada.strftime('%d/%m/%Y') if self.fecha_programada else None
        for user in calidad:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=self.fecha_programada or fields.Date.today(),
                summary=f'PDF actualizado — revisar {("antes del " + fecha_str) if fecha_str else ""}',
                note=f'El PDF del manual <b>{self.name}</b> fue actualizado. '
                     f'Por favor revisa los criterios con la nueva versión.',
                user_id=user.id,
            )

    def _notificar_revision_programada(self):
        """Fecha de revisión programada: avisar a toda Calidad (solo actividad Odoo)."""
        self.ensure_one()
        if not self.fecha_programada:
            return
        calidad = self._usuarios_calidad()
        fecha_str = self.fecha_programada.strftime('%d/%m/%Y')
        self.activity_ids.filtered(lambda a: 'Revisar' in (a.summary or '')).unlink()
        for user in calidad:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=self.fecha_programada,
                summary=f'Revisar manual antes del {fecha_str}',
                note=f'El manual <b>{self.name}</b> requiere revisión de Calidad '
                     f'antes del <b>{fecha_str}</b>.',
                user_id=user.id,
            )
        self.message_post(
            body=f'📅 Revisión programada para el <b>{fecha_str}</b>. '
                 f'Actividad enviada a {len(calidad)} persona(s) de Calidad.',
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
        )
