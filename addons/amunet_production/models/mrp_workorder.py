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

    def _check_amunet_operator_access(self):
        if not (
            self.env.user.has_group('amunet_production.group_production_operator')
            or self.env.user.has_group('amunet_production.group_production_supervisor')
            or self.env.user.has_group('mrp.group_mrp_user')
        ):
            raise AccessError(_('No tiene permisos para operar ordenes de trabajo de produccion.'))

    def action_amunet_operator_start(self):
        self._check_amunet_operator_access()
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
        if not self.env.user.has_group('amunet_production.group_production_supervisor'):
            raise AccessError(_(
                'Solo el supervisor de produccion puede recibir/aceptar el material entregado.'))

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_action_amunet_confirm_supply': _('Confirmar surtido AMP'),
            '_signature_action_amunet_receive_supply': _('Recibir surtido AMP'),
        }

    def _amunet_signature_required_procedures(self):
        self.ensure_one()
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
        for move in self.production_id.move_raw_ids:
            if move.state == 'cancel':
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
        return self.env['amunet.generic.signature.wizard'].open_for(
            self,
            '_signature_action_amunet_receive_supply',
            _('Recibir surtido AMP'),
            _('Firma de recepcion de surtido para %s.') % self.display_name,
        )

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
