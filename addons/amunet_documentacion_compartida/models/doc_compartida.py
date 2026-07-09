from datetime import timedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

_CAMPOS_REV = ['rev_materiales', 'rev_volumenes', 'rev_tiempos', 'rev_adicional']

JORGE_UID = 70  # único autorizado a editar fecha_programada


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
    state = fields.Selection(
        [('aprobado', 'APROBADO'), ('pendiente', 'PENDIENTE')],
        string='Estatus', default='pendiente',
        compute='_compute_estado', store=True, tracking=True)

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
        for rec in self:
            rec.es_responsable = (uid == JORGE_UID)
            rec.soy_revisor_activo = bool(rec.revisor_activo_id) and rec.revisor_activo_id.id == uid

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
            all_ok = all(r == 'ok' for r in reviews)
            any_fail = any(r == 'fail' for r in reviews)
            rec.state = 'aprobado' if all_ok else 'pendiente'
            rec.obs_requeridas = any_fail

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

        # Solo Jorge puede cambiar la fecha programada
        if 'fecha_programada' in vals and uid != JORGE_UID:
            raise UserError(
                'Solo el responsable de Validación puede modificar la fecha programada.')

        # Cualquier usuario del módulo puede marcar criterios.
        # Auto-registramos quién revisó y cuándo.
        campos_revision = {'rev_materiales', 'rev_volumenes', 'rev_tiempos', 'rev_adicional'}
        if campos_revision & set(vals):
            if not self.env.context.get('bypass_revisor_check'):
                vals['revisor_activo_id'] = uid
                vals['revisado_por_id'] = uid
                vals['fecha_revision'] = fields.Datetime.now()

        # Capturar estado y valores de criterios antes de escribir
        campos_revision = {'rev_materiales', 'rev_volumenes', 'rev_tiempos', 'rev_adicional'}
        criterios_cambiados = campos_revision & set(vals)
        state_antes = {}
        valores_antes = {}
        if criterios_cambiados:
            state_antes = {rec.id: rec.state for rec in self}
            valores_antes = {
                rec.id: {c: getattr(rec, c) for c in criterios_cambiados}
                for rec in self
            }

        result = super().write(vals)

        # Sincronizar observaciones según resultado final
        if criterios_cambiados and 'observaciones' not in vals:
            for rec in self:
                reviews = [rec.rev_materiales, rec.rev_volumenes, rec.rev_tiempos, rec.rev_adicional]
                all_ok = all(r == 'ok' for r in reviews)
                if all_ok and rec.observaciones != 'Ninguna':
                    rec._write({'observaciones': 'Ninguna'})
                elif any(r == 'fail' for r in reviews) and rec.observaciones == 'Ninguna':
                    rec._write({'observaciones': False})

        # Registrar cambios de criterio y cierre en historial
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
                if state_antes.get(rec.id) != 'aprobado' and rec.state == 'aprobado':
                    self.env['amunet.doc.revision.historial'].sudo().create({
                        'doc_id': rec.id,
                        'usuario_id': self.env.user.id,
                        'accion': 'cierre',
                    })
                    rec._notificar_diana_manual_aprobado()

        # Notificar a Calidad cuando se programa una fecha
        if 'fecha_programada' in vals and vals.get('fecha_programada'):
            for rec in self:
                rec._notificar_revision_programada()

        return result

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

    def _notificar_diana_manual_aprobado(self):
        self.ensure_one()
        diana_uid = 64
        ya_tiene = self.activity_ids.filtered(
            lambda a: a.user_id.id == diana_uid
            and 'aprobado' in (a.summary or '').lower()
        )
        if ya_tiene:
            return
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            date_deadline=fields.Date.today(),
            summary=f'Manual aprobado: {self.name}',
            note=f'El manual <b>{self.name}</b> ha sido <b>APROBADO</b> por Calidad.<br/>'
                 f'Entra al manual y selecciona <b>"Actualizar en sistema"</b> para notificar '
                 f'a Documentación y archivar la versión definitiva.',
            user_id=diana_uid,
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
            rec.with_context(bypass_revisor_check=True).write(
                {'revisor_activo_id': False})
            resultado = 'APROBADO ✓' if rec.state == 'aprobado' else 'CON OBSERVACIONES ✗'
            rec.message_post(
                body=f'✅ Revisión cerrada automáticamente por {revisor_nombre} '
                     f'(todas las columnas completadas, sin cambios por 1 minuto).',
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )
            # Notificar al responsable (Jorge) para que ejecute los cambios
            ya_tiene = rec.activity_ids.filtered(
                lambda a: a.user_id.id == JORGE_UID
                and 'Revisión lista' in (a.summary or '')
            )
            if not ya_tiene:
                rec.activity_schedule(
                    'mail.mail_activity_data_todo',
                    date_deadline=fields.Date.today(),
                    summary=f'Revisión lista: {rec.name}',
                    note=f'<b>{revisor_nombre}</b> completó la revisión de <b>{rec.name}</b>.<br/>'
                         f'Resultado: <b>{resultado}</b><br/>'
                         f'Entra al manual, revisa los criterios y ejecuta los cambios si aplica.',
                    user_id=JORGE_UID,
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
        self.ensure_one()
        grupo = self.env.ref(
            'amunet_documentacion_compartida.group_doc_compartida_user',
            raise_if_not_found=False)
        if not grupo:
            return
        destinatarios = grupo.user_ids.filtered(lambda u: u.id != self.env.user.id)
        partner_ids = destinatarios.mapped('partner_id').ids
        self.message_post(
            body=f'🔄 El PDF de <b>{self.name}</b> fue actualizado por '
                 f'<b>{self.env.user.name}</b>. '
                 f'Por favor revisen si los criterios siguen siendo válidos con la nueva versión.',
            partner_ids=partner_ids,
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
        )
        if self.fecha_programada:
            fecha_str = self.fecha_programada.strftime('%d/%m/%Y')
            for user in destinatarios:
                self.activity_schedule(
                    'mail.mail_activity_data_todo',
                    date_deadline=self.fecha_programada,
                    summary=f'PDF actualizado — revisar antes del {fecha_str}',
                    note=f'El PDF del manual <b>{self.name}</b> fue actualizado. '
                         f'Por favor revisa los cambios.',
                    user_id=user.id,
                )

    def _notificar_revision_programada(self):
        self.ensure_one()
        if not self.fecha_programada:
            return

        grupo = self.env.ref(
            'amunet_documentacion_compartida.group_doc_compartida_user',
            raise_if_not_found=False)
        if not grupo:
            return

        destinatarios = grupo.user_ids.filtered(lambda u: u.id != self.env.user.id)
        fecha_str = self.fecha_programada.strftime('%d/%m/%Y')

        # Cancelar actividades anteriores de revisión de este documento
        self.activity_ids.filtered(
            lambda a: 'Revisar' in (a.summary or '')
        ).unlink()

        # Crear una actividad por revisor
        for user in destinatarios:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=self.fecha_programada,
                summary=f'Revisar manual antes del {fecha_str}',
                note=f'El manual <b>{self.name}</b> requiere revisión de Calidad '
                     f'antes del <b>{fecha_str}</b>.',
                user_id=user.id,
            )

        # Mensaje en el chatter
        partner_ids = destinatarios.mapped('partner_id').ids
        self.message_post(
            body=f'📅 Revisión programada para el <b>{fecha_str}</b>. '
                 f'Notificación enviada a {len(destinatarios)} revisor(es) de Calidad.',
            partner_ids=partner_ids,
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
        )
