# -*- coding: utf-8 -*-
from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    amunet_operator_next_step = fields.Char(
        string='Siguiente paso',
        compute='_compute_amunet_operator_guidance',
    )
    amunet_operator_material_status = fields.Char(
        string='Materiales',
        compute='_compute_amunet_operator_guidance',
    )
    amunet_operator_quality_status = fields.Char(
        string='Calidad',
        compute='_compute_amunet_operator_guidance',
    )
    amunet_operator_time_status = fields.Char(
        string='Tiempo',
        compute='_compute_amunet_operator_guidance',
    )
    amunet_workqueue_priority = fields.Selection([
        ('ready', 'Listo'),
        ('progress', 'En curso'),
        ('waiting', 'En espera'),
        ('blocked', 'Bloqueado'),
        ('done', 'Terminado'),
    ], string='Prioridad cola', compute='_compute_amunet_workqueue')
    amunet_workqueue_owner = fields.Selection([
        ('production', 'Produccion'),
        ('supervisor', 'Supervisor'),
        ('warehouse', 'Almacen'),
        ('metrology', 'Metrologia'),
        ('quality', 'Calidad'),
        ('none', 'Sin accion'),
    ], string='Responsable', compute='_compute_amunet_workqueue')
    amunet_workqueue_next_step = fields.Char(
        string='Siguiente paso cola',
        compute='_compute_amunet_workqueue',
    )
    amunet_workqueue_blocker = fields.Char(
        string='Bloqueo / pendiente',
        compute='_compute_amunet_workqueue',
    )

    # ============================
    # Flujo de Surtido (workcenter AMP)
    # ============================
    # Espeja el flujo de amunet_material_request:
    #   pending             -> Almacen no inicia
    #   in_progress         -> Almacen surtiendo (timer corriendo)
    #   awaiting_reception  -> Almacen confirmo, espera firma de produccion
    #   received            -> Produccion valido, WO done, libera siguiente
    amunet_is_supply_workorder = fields.Boolean(
        string='Es surtido (AMP)',
        compute='_compute_is_supply_workorder',
        store=True,
    )
    amunet_supply_state = fields.Selection([
        ('pending', 'Pendiente de iniciar'),
        ('in_progress', 'Surtiendo'),
        ('awaiting_reception', 'Esperando recepcion de produccion'),
        ('received', 'Recibido'),
    ], string='Estado del surtido', default='pending', copy=False)
    amunet_supplied_by_id = fields.Many2one(
        'res.users', string='Surtido por', readonly=True, copy=False,
    )
    amunet_supplied_date = fields.Datetime(
        string='Fecha de surtido', readonly=True, copy=False,
    )
    amunet_received_by_id = fields.Many2one(
        'res.users', string='Recibido por', readonly=True, copy=False,
    )
    amunet_received_date = fields.Datetime(
        string='Fecha de recepcion', readonly=True, copy=False,
    )
    amunet_supply_moves = fields.One2many(
        related='production_id.move_raw_ids',
        string='Materiales a surtir',
    )

    @api.depends('workcenter_id.code')
    def _compute_is_supply_workorder(self):
        for wo in self:
            wo.amunet_is_supply_workorder = (wo.workcenter_id.code or '') == 'AMP'

    def _compute_amunet_operator_guidance(self):
        material_labels = {
            'assigned': 'Material disponible',
            'available': 'Material disponible',
            'confirmed': 'Material pendiente de surtir',
            'waiting': 'Esperando material u operacion previa',
            'late': 'Material con alerta',
            'unavailable': 'Material no disponible',
        }
        quality_labels = {
            'none': 'Sin QC requerido en esta orden',
            'to_request': 'Calidad pendiente de solicitud',
            'requested': 'Calidad solicitada',
            'approved': 'Calidad aprobada',
            'rejected': 'Calidad rechazada',
        }
        for wo in self:
            if wo.state == 'ready':
                next_step = 'Iniciar operacion'
            elif wo.state == 'progress':
                next_step = 'Terminar operacion o pausar'
            elif wo.state == 'blocked':
                next_step = 'Esperar operacion previa o materiales'
            elif wo.state == 'done':
                next_step = 'Operacion terminada'
            elif wo.state == 'cancel':
                next_step = 'Operacion cancelada'
            else:
                next_step = 'Revisar estado'

            availability = wo.production_availability or wo.production_id.reservation_state or ''
            wo.amunet_operator_next_step = next_step
            wo.amunet_operator_material_status = material_labels.get(
                availability,
                availability or 'Sin dato de materiales',
            )
            wo.amunet_operator_quality_status = quality_labels.get(
                wo.production_id.quality_analysis_status or 'none',
                wo.production_id.quality_analysis_status or 'Sin dato de calidad',
            )
            if wo.state == 'progress' and wo.is_user_working:
                wo.amunet_operator_time_status = 'Tu tiempo esta corriendo'
            elif wo.state == 'progress':
                wo.amunet_operator_time_status = 'Operacion en progreso'
            elif wo.duration:
                wo.amunet_operator_time_status = '%s min registrados' % round(wo.duration, 1)
            elif wo.duration_expected:
                wo.amunet_operator_time_status = '%s min estimados' % round(wo.duration_expected, 1)
            else:
                wo.amunet_operator_time_status = 'Sin tiempo registrado'

    def _amunet_equipment_blockers(self):
        self.ensure_one()
        wc = self.workcenter_id
        if not wc:
            return [_('Sin centro de trabajo asignado.')]
        if not hasattr(wc, 'amunet_equipment_ids'):
            return []
        if not wc.amunet_equipment_ids:
            if wc.amunet_no_equipment_required:
                if not (
                    wc.amunet_equipment_exception_reason
                    and wc.amunet_equipment_exception_signed_by_id
                    and wc.amunet_equipment_exception_signed_date
                ):
                    return [_('Excepcion de equipo sin firma completa en %s.') % (wc.code or wc.name)]
                return []
            return [_('Area %s sin equipos vinculados ni excepcion firmada.') % (wc.code or wc.name)]

        today = fields.Date.context_today(self)
        blockers = []
        for eq in wc.amunet_equipment_ids:
            if eq.state != 'active':
                label = dict(eq._fields['state'].selection).get(eq.state, eq.state)
                blockers.append(_('%s no operativo (%s).') % (eq.display_name, label))
                continue
            calibration = self.env['amunet.equipment.calibration'].search([
                ('equipment_id', '=', eq.id),
                ('state', '=', 'done'),
                ('expiration_date', '>=', today),
            ], limit=1)
            if not calibration:
                blockers.append(_('%s sin calibracion vigente.') % eq.display_name)
        return blockers

    def _compute_amunet_workqueue(self):
        state_labels = dict(self._fields['state'].selection)
        material_labels = {
            'assigned': _('Material disponible'),
            'available': _('Material disponible'),
            'confirmed': _('Material pendiente de surtir'),
            'waiting': _('Esperando material u operacion previa'),
            'late': _('Material con alerta'),
            'unavailable': _('Material no disponible'),
        }
        for wo in self:
            owner = 'production'
            priority = 'waiting'
            next_step = _('Revisar operacion')
            blocker = False

            if wo.state in ('done', 'cancel'):
                wo.amunet_workqueue_priority = 'done'
                wo.amunet_workqueue_owner = 'none'
                wo.amunet_workqueue_next_step = _('Sin accion')
                wo.amunet_workqueue_blocker = False
                continue

            if wo.amunet_is_supply_workorder:
                if wo.amunet_supply_state == 'pending':
                    owner = 'warehouse'
                    next_step = _('Almacen inicia surtido')
                    if wo.state != 'ready':
                        blocker = _('Surtido pendiente; la operacion aun esta %s.') % state_labels.get(wo.state, wo.state)
                elif wo.amunet_supply_state == 'in_progress':
                    owner = 'warehouse'
                    priority = 'progress'
                    next_step = _('Almacen confirma surtido con firma')
                elif wo.amunet_supply_state == 'awaiting_reception':
                    owner = 'supervisor'
                    priority = 'ready'
                    next_step = _('Supervisor recibe el surtido con firma')
                    blocker = _('Firma de recepcion de surtido pendiente.')
                elif wo.amunet_supply_state == 'received':
                    owner = 'production'
                    next_step = _('Surtido recibido; continuar ruta')

            if wo.state == 'ready':
                priority = 'ready'
                next_step = next_step if wo.amunet_is_supply_workorder else _('Iniciar operacion')
            elif wo.state == 'progress':
                priority = 'progress'
                next_step = next_step if wo.amunet_is_supply_workorder else _('Terminar operacion')
            elif wo.state in ('pending', 'waiting', 'blocked'):
                priority = 'blocked' if wo.state == 'blocked' else 'waiting'
                previous = wo.production_id.workorder_ids.filtered(
                    lambda w: w.id != wo.id
                    and w.state not in ('done', 'cancel')
                    and (w.sequence or 0) < (wo.sequence or 0)
                )
                availability = wo.production_availability or wo.production_id.reservation_state or ''
                if previous:
                    blocker = _('Operacion previa pendiente: %s') % ', '.join(previous[:3].mapped('name'))
                elif availability and availability not in ('assigned', 'available'):
                    blocker = material_labels.get(availability, availability)
                elif not blocker:
                    blocker = _('Operacion en estado %s; revisar ruta, materiales o disponibilidad.') % state_labels.get(wo.state, wo.state)
                next_step = _('Resolver bloqueo antes de iniciar')

            equipment_blockers = wo._amunet_equipment_blockers()
            if equipment_blockers and wo.state in ('ready', 'progress', 'blocked', 'waiting', 'pending'):
                priority = 'blocked'
                owner = 'metrology'
                blocker = '; '.join(equipment_blockers[:3])
                next_step = _('Corregir equipo/calibracion del area')

            wo.amunet_workqueue_priority = priority
            wo.amunet_workqueue_owner = owner
            wo.amunet_workqueue_next_step = next_step
            wo.amunet_workqueue_blocker = blocker

    def _check_amunet_operator_access(self):
        if not (
            self.env.user.has_group('amunet_production.group_production_operator')
            or self.env.user.has_group('amunet_production.group_production_supervisor')
            or self.env.user.has_group('mrp.group_mrp_user')
        ):
            raise AccessError(_('No tiene permisos para operar ordenes de trabajo de produccion.'))

    def _amunet_gate_preflight_solution(self):
        """Soluciones: no permitir EMPEZAR a colocar lotes ni pesados si el
        preflight de la orden no esta validado (aceptado). Aplica a TODAS las
        soluciones (desarrollo o no)."""
        for wo in self:
            prod = wo.production_id
            if prod and prod.amunet_is_solution_product and not prod.amunet_preflight_accepted:
                raise UserError(_(
                    'Antes de colocar lotes o registrar pesados, valida el preflight '
                    'de la orden %s: usa "Validar piloto" y luego "Aceptar para '
                    'piloto". No se puede iniciar el trabajo hasta que el preflight '
                    'este validado.') % (prod.name or ''))

    def action_amunet_operator_start(self):
        self._check_amunet_operator_access()
        self._amunet_gate_preflight_solution()
        for wo in self:
            if wo.state != 'ready':
                raise UserError(_('Solo se puede iniciar una operacion en estado Por realizar.'))
            wo.sudo().button_start()
            if wo.production_id:
                wo.production_id.sudo().message_post(
                    body=Markup(_(
                        'Operacion <b>%s</b> iniciada desde Mi trabajo de produccion por <b>%s</b>.'
                    ) % (wo.display_name, self.env.user.name)),
                    message_type='notification',
                )
        return True

    def action_amunet_operator_finish(self):
        self._check_amunet_operator_access()
        for wo in self:
            if wo.state != 'progress':
                raise UserError(_('Solo se puede terminar una operacion en progreso.'))
            wo.sudo().button_finish()
            if wo.production_id:
                wo.production_id.sudo().message_post(
                    body=Markup(_(
                        'Operacion <b>%s</b> terminada desde Mi trabajo de produccion por <b>%s</b>.'
                    ) % (wo.display_name, self.env.user.name)),
                    message_type='notification',
                )
        return True

    def action_amunet_open_production(self):
        self.ensure_one()
        view = self.env.ref(
            'amunet_production.view_mrp_production_operator_form',
            raise_if_not_found=False,
        )
        return {
            'type': 'ir.actions.act_window',
            'name': _('Orden de fabricacion'),
            'res_model': 'mrp.production',
            'res_id': self.production_id.id,
            'view_mode': 'form',
            'views': [(view.id, 'form')] if view else [(False, 'form')],
            'target': 'current',
        }

    # ============================
    # Acciones del flujo de Surtido (AMP)
    # ============================
    def _amunet_check_warehouse_role(self):
        if not (
            self.env.user.has_group('amunet_material_request.group_material_warehouse')
            or self.env.user.has_group('amunet_material_request.group_material_manager')
        ):
            raise AccessError(_(
                'Solo personal del grupo de Almacen puede surtir materiales.'))

    def _amunet_check_production_supervisor(self):
        # Operadores Y supervisores de produccion pueden recibir/aceptar el
        # material surtido (el supervisor hereda el grupo operador).
        if not self.env.user.has_group('amunet_production.group_production_operator'):
            raise AccessError(_(
                'Solo produccion (operador o supervisor) puede recibir/aceptar el material entregado.'))

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_action_amunet_confirm_supply': _('Confirmar surtido AMP'),
            '_signature_action_amunet_receive_supply': _('Recibir surtido AMP'),
        }

    def _amunet_signature_required_procedures(self):
        self.ensure_one()
        # La firma de RECEPCION/aceptacion de surtido no opera el equipo del
        # almacen (refri/termohigrometro): solo acepta el material entregado.
        # Por eso no debe exigir los SOPs de equipo del centro de trabajo de
        # almacen. La firma de SURTIDO (almacen) si los exige (sin este flag).
        if self.env.context.get('amunet_skip_equipment_training'):
            return self.env['amunet.quality.procedure']
        procedures = self.workcenter_id.amunet_equipment_ids.mapped('procedure_ids')
        if not procedures and self.production_id.product_id:
            procedures = self.env['amunet.quality.procedure'].search([
                ('active', '=', True),
                ('product_ids', 'in', self.production_id.product_id.id),
            ])
        return procedures.filtered('active')

    def action_amunet_start_supply(self):
        self.ensure_one()
        if not self.amunet_is_supply_workorder:
            raise UserError(_('Esta accion solo aplica al workorder de Surtido (AMP).'))
        self._amunet_check_warehouse_role()
        self._amunet_gate_preflight_solution()
        if self.amunet_supply_state != 'pending':
            raise UserError(_(
                'El surtido ya esta iniciado (estado actual: %s).') % self.amunet_supply_state)
        if self.state in ('done', 'cancel'):
            raise UserError(_('La operacion ya esta cerrada.'))
        if self.state in ('pending', 'waiting', 'blocked'):
            raise UserError(_(
                'La operacion no esta lista para iniciar. Confirme la MO '
                'o complete operaciones previas.'))
        self.sudo().button_start()
        self.write({'amunet_supply_state': 'in_progress'})
        # Autollenar 'Cantidad surtida' con la 'Cantidad por consumir'.
        # El almacenista solo la ajusta si surtio algo distinto. No se
        # pisa un valor ya capturado.
        if self.production_id:
            for move in self.production_id.sudo().move_raw_ids.filtered(
                    lambda m: m.state != 'cancel' and not m.amunet_qty_supplied):
                move.amunet_qty_supplied = move.product_uom_qty
        # Una vez que un almacenista toma el surtido, cerramos las
        # actividades pendientes del resto del grupo (mismo patron que
        # amunet_material_request).
        if self.production_id:
            self.production_id._amunet_close_warehouse_supply_activities()
            self.production_id.sudo().message_post(body=Markup(_(
                'Surtido de materiales iniciado por <b>%s</b>.'
            )) % self.env.user.name)
        return True

    def action_amunet_confirm_supply(self):
        self.ensure_one()
        if not self.amunet_is_supply_workorder:
            raise UserError(_('Esta accion solo aplica al workorder de Surtido (AMP).'))
        self._amunet_check_warehouse_role()
        if self.amunet_supply_state != 'in_progress':
            raise UserError(_(
                'Solo se puede confirmar surtido cuando esta en progreso.'))
        return self.env['amunet.generic.signature.wizard'].open_for(
            self,
            '_signature_action_amunet_confirm_supply',
            _('Confirmar surtido AMP'),
            _('Firma de confirmacion de surtido para %s.') % self.display_name,
        )

    def _signature_action_amunet_confirm_supply(self):
        """Almacen confirma surtido: valida lote + cantidad surtida en
        cada componente raw, corta el intervalo del timer (sin cerrar
        la WO), deja la WO esperando recepcion de produccion y notifica.
        Espeja amunet_material_request.action_confirm_delivery.
        """
        self.ensure_one()
        if not self.amunet_is_supply_workorder:
            raise UserError(_('Esta accion solo aplica al workorder de Surtido (AMP).'))
        self._amunet_check_warehouse_role()
        if self.amunet_supply_state != 'in_progress':
            raise UserError(_(
                'Solo se puede confirmar surtido cuando esta en progreso.'))
        # Validacion espejo de amunet_material_request (lineas 564-582):
        # cada componente debe tener qty_supplied > 0 y, si el producto
        # es trazable, lote asignado en move_line_ids.
        errores = []
        es_solucion = self.production_id.amunet_is_solution_product
        for move in self.production_id.move_raw_ids:
            if move.state == 'cancel':
                continue
            # En SOLUCIONES solo se surten las sub-soluciones (needs_surtido);
            # los reactivos vienen de ARU y no se surten dentro de la orden.
            if es_solucion and not move.amunet_needs_surtido:
                continue
            if (move.amunet_qty_supplied or 0.0) <= 0.0:
                errores.append(_(
                    '  - %s: cantidad surtida = 0'
                ) % move.product_id.display_name)
                continue
            tracking = move.product_id.tracking
            if tracking in ('lot', 'serial'):
                lotes_validos = move.move_line_ids.filtered(lambda l: l.lot_id)
                if not lotes_validos:
                    errores.append(_(
                        '  - %s: hay cantidades sin lote asignado'
                    ) % move.product_id.display_name)
        if errores:
            raise UserError(_(
                'Faltan datos por capturar:\n%s'
            ) % '\n'.join(errores))
        # Pausar timer sin cerrar la WO.
        if hasattr(self, 'end_all'):
            self.sudo().end_all()
        elif hasattr(self, 'end_previous'):
            self.sudo().end_previous(doall=True)
        now = fields.Datetime.now()
        self.with_context(amunet_supply_signature_write=True).write({
            'amunet_supply_state': 'awaiting_reception',
            'amunet_supplied_by_id': self.env.user.id,
            'amunet_supplied_date': now,
        })
        if self.production_id:
            self.production_id._amunet_notify_production_supply_ready()
            self.production_id.sudo().message_post(body=Markup(_(
                'Surtido confirmado por almacen (<b>%s</b>). '
                'Esperando recepcion de produccion.'
            )) % self.env.user.name)
        return True

    def action_amunet_receive_supply(self):
        self.ensure_one()
        if not self.amunet_is_supply_workorder:
            raise UserError(_('Esta accion solo aplica al workorder de Surtido (AMP).'))
        self._amunet_check_production_supervisor()
        if self.amunet_supply_state != 'awaiting_reception':
            raise UserError(_(
                'No hay surtido pendiente de recepcion en esta operacion.'))
        action = self.env['amunet.generic.signature.wizard'].open_for(
            self,
            '_signature_action_amunet_receive_supply',
            _('Recibir surtido AMP'),
            _('Firma de recepcion de surtido para %s.') % self.display_name,
        )
        # La recepcion no exige capacitacion de equipo del almacen (ver
        # _amunet_signature_required_procedures): solo se acepta el material.
        action.setdefault('context', {})['amunet_skip_equipment_training'] = True
        return action

    def _signature_action_amunet_receive_supply(self):
        """Produccion recibe/acepta el material entregado: copia
        qty_supplied -> quantity (conciliacion del surtido), cierra la
        WO (libera siguiente operacion) y notifica.
        """
        self.ensure_one()
        if not self.amunet_is_supply_workorder:
            raise UserError(_('Esta accion solo aplica al workorder de Surtido (AMP).'))
        self._amunet_check_production_supervisor()
        if self.amunet_supply_state != 'awaiting_reception':
            raise UserError(_(
                'No hay surtido pendiente de recepcion en esta operacion.'))
        # Conciliacion del surtido: copiamos qty_supplied -> quantity
        # en cada componente raw para que la MO refleje lo entregado.
        # Produccion puede ajustar mas adelante (en button_mark_done).
        for move in self.production_id.move_raw_ids:
            if move.state == 'cancel':
                continue
            qty = move.amunet_qty_supplied or 0.0
            if qty > 0:
                move.sudo().write({'quantity': qty})
        # Cerrar la WO -> libera la siguiente en la ruta.
        self.sudo().button_finish()
        now = fields.Datetime.now()
        self.with_context(amunet_supply_signature_write=True).write({
            'amunet_supply_state': 'received',
            'amunet_received_by_id': self.env.user.id,
            'amunet_received_date': now,
        })
        if self.production_id:
            self.production_id._amunet_close_production_supply_activities()
            self.production_id.sudo().message_post(body=Markup(_(
                'Surtido recibido y aceptado por produccion (<b>%s</b>). '
                'Liberando siguiente operacion.'
            )) % self.env.user.name)
        return True

    def _has_supply_signature_values(self, vals):
        signature_fields = {
            'amunet_supplied_by_id', 'amunet_supplied_date',
            'amunet_received_by_id', 'amunet_received_date',
        }
        signature_state = vals.get('amunet_supply_state') in (
            'awaiting_reception', 'received')
        return signature_state or set(vals).intersection(signature_fields)

    @api.model_create_multi
    def create(self, vals_list):
        if (
            not self.env.context.get('amunet_supply_signature_write')
            and not self.env.su
        ):
            for vals in vals_list:
                if self._has_supply_signature_values(vals):
                    raise UserError(_(
                        'La confirmacion y recepcion del surtido AMP solo '
                        'pueden registrarse desde el wizard de firma electronica.'))
        return super().create(vals_list)

    def write(self, vals):
        if (
            self._has_supply_signature_values(vals)
            and not self.env.context.get('amunet_supply_signature_write')
            and not self.env.su
        ):
            raise UserError(_(
                'La confirmacion y recepcion del surtido AMP solo pueden '
                'registrarse desde el wizard de firma electronica.'))
        return super().write(vals)

    def button_start(self):
        """Valida calibraciones / estado de equipos antes de arrancar.

        Si workcenter_id._amunet_check_equipment_calibration falla,
        levanta UserError. Si pasa pero el WC tiene
        amunet_no_equipment_required=True, registra una nota en el
        chatter de la mrp.production relacionada (mrp.workorder no es
        mail.thread; el log queda en la MO padre, donde es visible y
        auditable).
        """
        for wo in self:
            wc = wo.workcenter_id
            if not wc:
                continue
            # Validacion por ACTIVIDAD si la operacion la define; si no, el
            # metodo de la operacion delega al centro de trabajo (comportamiento
            # anterior). Sin operacion ligada, se valida por centro de trabajo.
            op = wo.operation_id
            if op and hasattr(op, '_amunet_check_operation_equipment'):
                res = op._amunet_check_operation_equipment() or {}
            else:
                res = wc._amunet_check_equipment_calibration() or {}
            if res.get('no_equipment_required') and wo.production_id:
                wo.production_id.message_post(body=_(
                    'WO <b>%s</b> (id=%s) iniciada sin equipos calibrados. '
                    'Workcenter <b>%s</b> esta marcado como '
                    '"No requiere equipo calibrado" '
                    '(amunet_no_equipment_required=True). '
                    'Excepcion autorizada en configuracion del WC. '
                    'Justificacion ISO 13485 debe estar documentada en '
                    'la nota del workcenter o en CAPA.'
                ) % (wo.name or wo.id, wo.id, wc.code or wc.name))
        return super().button_start()
