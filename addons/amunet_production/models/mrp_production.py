# -*- coding: utf-8 -*-
from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError, ValidationError
from markupsafe import Markup

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.constrains('product_id', 'state')
    def _amunet_check_no_duplicate_draft(self):
        """Bloquea crear/tener otra orden de produccion del mismo producto
        si ya existe una en Borrador."""
        for mo in self:
            if mo.state == 'draft' and mo.product_id:
                otra = self.search([
                    ('id', '!=', mo.id),
                    ('product_id', '=', mo.product_id.id),
                    ('state', '=', 'draft'),
                ], limit=1)
                if otra:
                    raise ValidationError(_(
                        'Ya existe una orden de produccion en Borrador para '
                        '"%(prod)s" (%(mo)s). Confirmala o eliminala antes de '
                        'crear otra del mismo producto.'
                    ) % {'prod': mo.product_id.display_name, 'mo': otra.name})

    # Campos requeridos para Módulo de Soluciones
    quality_ph_initial = fields.Float(string='pH Inicial Objetivo', compute='_compute_quality_params', store=True, readonly=False)
    quality_ph_final = fields.Float(string='pH Final Obtenido')
    solution_lot_id = fields.Char(string='Lote de produccion', copy=False, help="Lote asignado al producto final (interno)")

    amunet_scheduled_date_display = fields.Char(
        string='Fecha Programada',
        compute='_compute_scheduled_date_display',
        inverse='_inverse_scheduled_date_display',
        store=False
    )
    
    solution_expiration_date = fields.Datetime(string='Fecha de Caducidad (Calendario)', compute='_compute_quality_params', store=True, readonly=False)
    amunet_expiration_text = fields.Char(string='Caducidad (Texto)', compute='_compute_quality_params', store=True, readonly=False)
    
    # Checklist Operativa (Actividades de Fabricación)
    amunet_check_history_log = fields.Boolean(string='Registro en Bitácoras', tracking=True)
    amunet_check_calculations = fields.Boolean(string='Cálculos Realizados', tracking=True)
    amunet_check_dilution = fields.Boolean(string='Dilución Realizada', tracking=True)
    amunet_check_aforar = fields.Boolean(string='Aforado Correcto', tracking=True)

    # Configuración arrastrada desde la plantilla
    amunet_sys_req_history = fields.Boolean(related='product_id.amunet_req_history_log')
    amunet_sys_req_calc = fields.Boolean(related='product_id.amunet_req_calculations')
    amunet_sys_weighing_range = fields.Char(string='Rango de Pesaje Operativo', compute='_compute_quality_params', store=True, readonly=False)
    amunet_sys_req_dilution = fields.Boolean(related='product_id.amunet_req_dilution')
    amunet_sys_ph_range = fields.Char(related='product_id.amunet_ph_adj_range_text')
    amunet_sys_req_aforar = fields.Boolean(related='product_id.amunet_req_aforar')
    
    # Campo lógico bidireccional hacia la plantilla del producto nativa (qc_required)
    amunet_sys_req_qc = fields.Boolean(
        string='Requiere Análisis C.C',
        related='product_id.qc_required', readonly=False, tracking=True,
        help="Permite anular o activar el pase por laboratorio bilateralmente."
    )
    
    quality_analysis_status = fields.Selection([
        ('none', 'No Requerido'),
        ('to_request', 'Pendiente de Solicitar'),
        ('requested', 'Análisis Solicitado'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado')
    ], string='Integración de Calidad', default='none', tracking=True, compute='_compute_quality_params', store=True, readonly=False)

    amunet_all_ingredients_valid = fields.Boolean(
        compute='_compute_all_ingredients_valid',
        string='Todos los ingredientes validos'
    )

    amunet_product_categ_id = fields.Many2one(
        'product.category',
        string='Categoria',
        compute='_compute_product_categ',
        store=False,
    )

    amunet_is_solution_product = fields.Boolean(
        string='Es solucion',
        compute='_compute_product_categ',
        store=False,
    )

    # Surtido a nivel MO: vinculos al workorder de Surtido (AMP) para
    # exponer los botones del flujo (Iniciar/Confirmar/Recibir) en la
    # vista MO sin que el almacenista tenga que abrir el workorder.
    amunet_supply_workorder_id = fields.Many2one(
        'mrp.workorder',
        string='Workorder de Surtido',
        compute='_compute_amunet_supply_workorder',
        store=True,
    )
    amunet_supply_state = fields.Selection(
        related='amunet_supply_workorder_id.amunet_supply_state',
        string='Estado del surtido',
        store=True,
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

    @api.depends('workorder_ids.workcenter_id.code')
    def _compute_amunet_supply_workorder(self):
        for mo in self:
            wo = mo.workorder_ids.filtered(
                lambda w: (w.workcenter_id.code or '') == 'AMP'
            )[:1]
            mo.amunet_supply_workorder_id = wo or False

    @api.depends(
        'state',
        'workorder_ids.state',
        'workorder_ids.amunet_supply_state',
        'workorder_ids.workcenter_id',
        'amunet_supply_state',
        'quality_analysis_status',
        'reconciliation_state',
        'move_raw_ids.amunet_qty_supplied',
        'move_raw_ids.state',
    )
    def _compute_amunet_workqueue(self):
        state_labels = dict(self._fields['state'].selection)
        quality_labels = dict(self._fields['quality_analysis_status'].selection)
        reconciliation_labels = dict(self._fields['reconciliation_state'].selection)
        for mo in self:
            priority = 'waiting'
            owner = 'supervisor'
            next_step = _('Revisar orden')
            blocker = False

            if mo.state in ('done', 'cancel'):
                mo.amunet_workqueue_priority = 'done'
                mo.amunet_workqueue_owner = 'none'
                mo.amunet_workqueue_next_step = _('Sin accion')
                mo.amunet_workqueue_blocker = False
                continue

            if mo.state == 'draft':
                priority = 'waiting'
                owner = 'supervisor'
                next_step = _('Confirmar orden de fabricacion')
                blocker = _('Orden en borrador.')
            elif (
                mo.amunet_supply_workorder_id
                and mo.amunet_supply_workorder_id.amunet_workqueue_priority == 'blocked'
            ):
                wo = mo.amunet_supply_workorder_id
                priority = 'blocked'
                owner = wo.amunet_workqueue_owner or 'supervisor'
                next_step = _('Resolver bloqueo en %s') % (wo.name or wo.display_name)
                blocker = wo.amunet_workqueue_blocker
            elif mo.amunet_supply_workorder_id and mo.amunet_supply_state in (
                'pending', 'in_progress', 'awaiting_reception'
            ):
                if mo.amunet_supply_state == 'pending':
                    priority = 'ready'
                    owner = 'warehouse'
                    next_step = _('Almacen inicia surtido')
                    blocker = _('Surtido de materiales pendiente.')
                elif mo.amunet_supply_state == 'in_progress':
                    priority = 'progress'
                    owner = 'warehouse'
                    next_step = _('Almacen confirma surtido con firma')
                    blocker = _('Surtido iniciado; falta confirmarlo.')
                else:
                    priority = 'ready'
                    owner = 'supervisor'
                    next_step = _('Supervisor recibe surtido con firma')
                    blocker = _('Surtido pendiente de recepcion por Produccion.')
            else:
                open_workorders = mo.workorder_ids.filtered(
                    lambda w: w.state not in ('done', 'cancel')
                )
                blocked_workorders = open_workorders.filtered(
                    lambda w: w.amunet_workqueue_priority == 'blocked'
                )
                in_progress = open_workorders.filtered(lambda w: w.state == 'progress')
                ready = open_workorders.filtered(lambda w: w.state == 'ready')

                if blocked_workorders:
                    wo = blocked_workorders[0]
                    priority = 'blocked'
                    owner = wo.amunet_workqueue_owner or 'supervisor'
                    next_step = _('Resolver bloqueo en %s') % (wo.name or wo.display_name)
                    blocker = wo.amunet_workqueue_blocker
                elif in_progress:
                    priority = 'progress'
                    owner = 'production'
                    next_step = _('Terminar operaciones en curso')
                    blocker = _('%s operacion(es) en progreso.') % len(in_progress)
                elif ready:
                    priority = 'ready'
                    owner = 'production'
                    next_step = _('Iniciar operaciones listas')
                    blocker = _('%s operacion(es) listas para ejecutar.') % len(ready)
                elif open_workorders:
                    wo = open_workorders[0]
                    priority = 'waiting'
                    owner = wo.amunet_workqueue_owner or 'supervisor'
                    next_step = wo.amunet_workqueue_next_step or _('Revisar operaciones pendientes')
                    blocker = wo.amunet_workqueue_blocker or _('%s operacion(es) pendientes.') % len(open_workorders)
                else:
                    has_supply = any(
                        (m.amunet_qty_supplied or 0) > 0
                        for m in mo.move_raw_ids.filtered(lambda m: m.state != 'cancel')
                    )
                    if has_supply and mo.reconciliation_state != 'completed':
                        if mo.reconciliation_state == 'pending':
                            priority = 'ready'
                            owner = 'production'
                            next_step = _('Iniciar conciliacion de materiales')
                        elif mo.reconciliation_state == 'initiated':
                            priority = 'ready'
                            owner = 'supervisor'
                            next_step = _('Validar conciliacion')
                        else:
                            priority = 'ready'
                            owner = 'warehouse'
                            next_step = _('Confirmar devolucion recibida')
                        blocker = _('Conciliacion: %s') % reconciliation_labels.get(
                            mo.reconciliation_state, mo.reconciliation_state)
                    elif mo.amunet_sys_req_qc and mo.quality_analysis_status != 'approved':
                        if mo.quality_analysis_status in ('to_request', 'rejected'):
                            priority = 'ready'
                            owner = 'supervisor'
                            next_step = _('Solicitar analisis a Calidad')
                        else:
                            priority = 'waiting'
                            owner = 'quality'
                            next_step = _('Esperar aprobacion de Calidad')
                        blocker = _('Calidad: %s') % quality_labels.get(
                            mo.quality_analysis_status, mo.quality_analysis_status)
                    elif mo.amunet_can_produce:
                        priority = 'ready'
                        owner = 'supervisor'
                        next_step = _('Producir / cerrar orden')
                        blocker = False
                    else:
                        priority = 'waiting'
                        owner = 'supervisor'
                        next_step = _('Revisar cierre de orden')
                        blocker = _('Estado MO: %s') % state_labels.get(mo.state, mo.state)

            mo.amunet_workqueue_priority = priority
            mo.amunet_workqueue_owner = owner
            mo.amunet_workqueue_next_step = next_step
            mo.amunet_workqueue_blocker = blocker

    def action_amunet_mo_start_supply(self):
        self.ensure_one()
        if not self.amunet_supply_workorder_id:
            raise UserError(_('Esta orden no tiene workorder de Surtido (AMP).'))
        return self.amunet_supply_workorder_id.action_amunet_start_supply()

    def action_amunet_mo_confirm_supply(self):
        self.ensure_one()
        if not self.amunet_supply_workorder_id:
            raise UserError(_('Esta orden no tiene workorder de Surtido (AMP).'))
        res = self.amunet_supply_workorder_id.action_amunet_confirm_supply()
        # Candado ISO: un solo lote por componente (bloqueo temprano al surtir).
        self.move_raw_ids._amunet_check_single_lot_per_component()
        return res

    def action_amunet_mo_receive_supply(self):
        self.ensure_one()
        if not self.amunet_supply_workorder_id:
            raise UserError(_('Esta orden no tiene workorder de Surtido (AMP).'))
        return self.amunet_supply_workorder_id.action_amunet_receive_supply()

    # Ocultar botones nativos de produccion (Produce / Produce All)
    # El boton "Producir" Amunet vive al final del header y se controla
    # con amunet_can_produce. Los nativos siempre False para que el
    # nativo button_mark_done quede oculto.
    show_produce = fields.Boolean(compute='_compute_show_produce_amunet', store=False)
    show_produce_all = fields.Boolean(compute='_compute_show_produce_amunet', store=False)

    def _compute_show_produce_amunet(self):
        for rec in self:
            rec.show_produce = False
            rec.show_produce_all = False

    # Boton "Producir" Amunet: visible solo cuando la MO esta en una
    # fase donde tiene sentido cerrar y TODAS las workorders estan
    # concluidas (done o cancel). Si la MO no tiene workorders se
    # habilita en cuanto entra a confirmed/progress/to_close.
    # ─── Conciliación de materiales ──────────────────────────────────────
    reconciliation_state = fields.Selection([
        ('pending',    'Pendiente'),
        ('initiated',  'En proceso'),
        ('validated',  'Supervisada'),
        ('completed',  'Completada'),
    ], string='Conciliación', default='pending', copy=False, tracking=True)

    reconciliation_initiated_by = fields.Many2one(
        'res.users', string='Iniciada por', readonly=True, copy=False)
    reconciliation_initiated_date = fields.Datetime(
        string='Fecha inicio', readonly=True, copy=False)
    reconciliation_validated_by = fields.Many2one(
        'res.users', string='Validada por', readonly=True, copy=False)
    reconciliation_validated_date = fields.Datetime(
        string='Fecha validación', readonly=True, copy=False)
    reconciliation_completed_by = fields.Many2one(
        'res.users', string='Confirmada por', readonly=True, copy=False)
    reconciliation_completed_date = fields.Datetime(
        string='Fecha confirmación', readonly=True, copy=False)
    reconciliation_notes = fields.Text(
        string='Notas', copy=False)

    reconciliation_has_surplus = fields.Boolean(
        compute='_compute_reconciliation_has_surplus', store=False)
    amunet_has_supplied_moves = fields.Boolean(
        compute='_compute_amunet_has_supplied_moves', store=False)
    amunet_all_workorders_done = fields.Boolean(
        compute='_compute_amunet_all_workorders_done', store=False)
    amunet_user_is_warehouse = fields.Boolean(
        compute='_compute_amunet_user_is_warehouse', store=False)
    amunet_user_can_see_supply_details = fields.Boolean(
        compute='_compute_amunet_user_can_see_supply_details', store=False)

    @api.depends('move_raw_ids.amunet_qty_supplied', 'move_raw_ids.amunet_qty_used')
    def _compute_reconciliation_has_surplus(self):
        for rec in self:
            rec.reconciliation_has_surplus = any(
                (m.amunet_qty_supplied or 0) - (m.amunet_qty_used or 0) > 0.001
                for m in rec.move_raw_ids.filtered(lambda m: m.state != 'cancel')
            )

    @api.depends('move_raw_ids.amunet_qty_supplied', 'move_raw_ids.state')
    def _compute_amunet_has_supplied_moves(self):
        for rec in self:
            rec.amunet_has_supplied_moves = any(
                (m.amunet_qty_supplied or 0) > 0
                for m in rec.move_raw_ids.filtered(lambda m: m.state != 'cancel')
            )

    @api.depends('workorder_ids.state')
    def _compute_amunet_all_workorders_done(self):
        for rec in self:
            if not rec.workorder_ids:
                rec.amunet_all_workorders_done = True
            else:
                rec.amunet_all_workorders_done = all(
                    wo.state in ('done', 'cancel') for wo in rec.workorder_ids
                )

    @api.depends_context('uid')
    def _compute_amunet_user_is_warehouse(self):
        user = self.env.user
        is_wh = (
            user.has_group('amunet_material_request.group_material_warehouse')
            or user.has_group('amunet_material_request.group_material_manager')
        ) and not (
            user.has_group('amunet_production.group_production_supervisor')
            or user.has_group('amunet_production.group_production_operator')
            or user.has_group('mrp.group_mrp_manager')
            or user.has_group('mrp.group_mrp_user')
        )
        for rec in self:
            rec.amunet_user_is_warehouse = is_wh

    @api.depends_context('uid')
    def _compute_amunet_user_can_see_supply_details(self):
        # La columna "Detalles" de componentes es informacion de almacen.
        # La ven los grupos de almacen y los administradores del sistema
        # (Mery, Fernando). Produccion pura NO la ve.
        user = self.env.user
        can_see = (
            user.has_group('amunet_material_request.group_material_warehouse')
            or user.has_group('amunet_material_request.group_material_manager')
            or user.has_group('base.group_system')
        )
        for rec in self:
            rec.amunet_user_can_see_supply_details = can_see

    def action_initiate_reconciliation(self):
        self.ensure_one()
        if self.state not in ('confirmed', 'progress', 'to_close', 'done'):
            raise UserError(_('Solo se puede iniciar conciliación cuando la orden está en progreso.'))
        if self.reconciliation_state != 'pending':
            raise UserError(_('La conciliación ya fue iniciada.'))
        # Precargar qty_used = qty_supplied como punto de partida
        for move in self.move_raw_ids.filtered(
            lambda m: m.state != 'cancel' and (m.amunet_qty_supplied or 0) > 0
        ):
            if not move.amunet_qty_used:
                move.amunet_qty_used = move.amunet_qty_supplied
        self.write({
            'reconciliation_state': 'initiated',
            'reconciliation_initiated_by': self.env.user.id,
            'reconciliation_initiated_date': fields.Datetime.now(),
        })
        self.message_post(body=_('Conciliación de materiales iniciada por <b>%s</b>.') % self.env.user.name)

    def action_validate_reconciliation(self):
        self.ensure_one()
        if self.reconciliation_state != 'initiated':
            raise UserError(_('La conciliación debe estar en proceso para validarla.'))
        moves = self.move_raw_ids.filtered(
            lambda m: m.state != 'cancel' and (m.amunet_qty_supplied or 0) > 0
        )
        sin_uso = moves.filtered(lambda m: not m.amunet_qty_used or m.amunet_qty_used <= 0)
        if sin_uso:
            nombres = ', '.join(sin_uso.mapped('product_id.display_name'))
            raise UserError(_('Falta cantidad utilizada para: %s') % nombres)
        # Actualizar quantity = qty_used (lo que Odoo consumirá al validar la MO)
        for move in moves:
            move.sudo().write({'quantity': move.amunet_qty_used})
        # Si no hay sobrante, completar automáticamente sin esperar confirmación de almacén
        has_surplus = any(
            (m.amunet_qty_supplied or 0) - (m.amunet_qty_used or 0) > 0.001
            for m in moves
        )
        new_state = 'validated' if has_surplus else 'completed'
        self.write({
            'reconciliation_state': new_state,
            'reconciliation_validated_by': self.env.user.id,
            'reconciliation_validated_date': fields.Datetime.now(),
        })
        lines = []
        for m in moves:
            surplus = (m.amunet_qty_supplied or 0) - (m.amunet_qty_used or 0)
            if surplus > 0.001:
                uom = m.product_uom.name if m.product_uom else ''
                lines.append('- %s: <b>%.4g %s</b> a devolver' % (
                    m.product_id.display_name, surplus, uom))
        msg = _('Conciliación validada por <b>%s</b>.') % self.env.user.name
        if lines:
            msg += _('<br/>Sobrante a devolver a almacén:<br/>') + '<br/>'.join(lines)
        else:
            msg += _('<br/>Sin sobrante — conciliación completada automáticamente.')
        self.message_post(body=msg)

    def action_complete_reconciliation(self):
        self.ensure_one()
        if self.reconciliation_state != 'validated':
            raise UserError(_('Solo se puede confirmar la devolución cuando la conciliación está supervisada.'))
        self.write({
            'reconciliation_state': 'completed',
            'reconciliation_completed_by': self.env.user.id,
            'reconciliation_completed_date': fields.Datetime.now(),
        })
        self.message_post(body=_('Devolución de material sobrante confirmada por almacén (<b>%s</b>). Conciliación completada.') % self.env.user.name)
    # ─────────────────────────────────────────────────────────────────────

    amunet_can_produce = fields.Boolean(
        compute='_compute_amunet_can_produce', store=False,
        string='Listo para producir',
    )

    @api.depends(
        'state', 'workorder_ids.state', 'amunet_sys_req_qc', 'quality_analysis_status',
        'reconciliation_state', 'move_raw_ids.amunet_qty_supplied', 'move_raw_ids.state',
    )
    def _compute_amunet_can_produce(self):
        for rec in self:
            if rec.state not in ('confirmed', 'progress', 'to_close'):
                rec.amunet_can_produce = False
                continue
            if rec.workorder_ids:
                wos_done = all(wo.state in ('done', 'cancel') for wo in rec.workorder_ids)
            else:
                wos_done = True
            qc_ok = True
            if rec.amunet_sys_req_qc:
                qc_ok = rec.quality_analysis_status == 'approved'
            # Gate de conciliación: si hay material surtido, debe estar conciliado.
            has_supply = any(
                (m.amunet_qty_supplied or 0) > 0
                for m in rec.move_raw_ids.filtered(lambda m: m.state != 'cancel')
            )
            reconciliation_ok = not has_supply or rec.reconciliation_state == 'completed'
            rec.amunet_can_produce = wos_done and qc_ok and reconciliation_ok

    @api.depends('product_id')
    def _compute_product_categ(self):
        for rec in self:
            category = rec.product_id.categ_id if rec.product_id else False
            category_name = (category.complete_name or category.name or '') if category else ''
            rec.amunet_product_categ_id = category
            rec.amunet_is_solution_product = 'solucion' in category_name.lower()

    @api.depends('product_id', 'date_start')
    def _compute_quality_params(self):
        for rec in self:
            if not rec.product_id:
                rec.quality_ph_initial = False
                rec.amunet_expiration_text = False
                rec.amunet_sys_weighing_range = False
                rec.quality_analysis_status = 'none'
                rec.solution_expiration_date = False
                continue

            product = rec.product_id
            rec.quality_ph_initial = product.amunet_initial_ph
            rec.amunet_sys_weighing_range = product.amunet_weighing_range_text

            if product.amunet_req_quality_control:
                rec.quality_analysis_status = 'to_request'
            else:
                rec.quality_analysis_status = 'none'

            # Calculo de caducidad en formato Amunet "YYYY-MM":
            # 1. Si el producto define duracion (amunet_expiration_text
            #    del template, ej. "24 meses" o "2 años"), se usa esa.
            # 2. Si NO define duracion, default Amunet = 2 anos (24 meses).
            # El campo en la MO sigue editable manualmente para
            # excepciones.
            from datetime import timedelta
            from dateutil.relativedelta import relativedelta
            DEFAULT_MONTHS = 24  # 2 anos
            base_text = product.amunet_expiration_text or ''
            txt = base_text.lower()
            months_to_add = DEFAULT_MONTHS
            try:
                val = float(
                    ''.join(c for c in txt if c.isdigit() or c == '.'))
                if 'año' in txt or 'ano' in txt:
                    months_to_add = int(val * 12)
                elif 'mes' in txt:
                    months_to_add = int(val)
                elif 'dia' in txt or 'día' in txt:
                    months_to_add = int(val / 30) or DEFAULT_MONTHS
            except Exception:
                # texto del producto no parseable -> usar default 24 meses
                pass

            base_date = rec.date_start or fields.Datetime.now()
            expiration = base_date + relativedelta(months=months_to_add)
            rec.solution_expiration_date = expiration
            # Formato exacto pedido por el operador: YYYY-MM
            rec.amunet_expiration_text = expiration.strftime('%Y-%m')

    @api.constrains('amunet_expiration_text')
    def _check_expiration_text_format(self):
        """Valida el formato YYYY-MM cuando el usuario edita manualmente."""
        import re
        pattern = re.compile(r'^\d{4}-(0[1-9]|1[0-2])$')
        for rec in self:
            if rec.amunet_expiration_text and not pattern.match(
                    rec.amunet_expiration_text):
                from odoo.exceptions import ValidationError
                raise ValidationError(_(
                    'El formato de caducidad debe ser YYYY-MM '
                    '(ejemplo: 2026-05). Recibido: "%s"'
                ) % rec.amunet_expiration_text)

    @api.onchange('product_id')
    def _onchange_product_expiration(self):
        """Asigna campos de caducidad/pH y garantiza enlace de BoM al cambiar producto"""
        from datetime import timedelta
        product = self.product_id
        if not product:
            self.solution_expiration_date = False
            self.amunet_expiration_text = False
            self.quality_ph_initial = False
            self.bom_id = False
            return

        # Forzar enlace de BoM si no esta asignado (Odoo 19: el metodo nativo puede no correr antes)
        if not self.bom_id:
            bom_results = self.env['mrp.bom']._bom_find(
                product,
                company_id=self.company_id.id,
                bom_type='normal',
            )
            bom = bom_results.get(product, False)
            if bom:
                self.bom_id = bom

        self.amunet_expiration_text = product.amunet_expiration_text
        self.quality_ph_initial = product.amunet_initial_ph

        days_to_add = 0
        if product.amunet_expiration_text:
            txt = product.amunet_expiration_text.lower()
            try:
                val = float(''.join(c for c in txt if c.isdigit() or c == '.'))
                if 'mes' in txt: days_to_add = val * 30
                elif 'año' in txt or 'ano' in txt: days_to_add = val * 365
                elif 'dia' in txt or 'día' in txt: days_to_add = val
            except:
                pass
        self.solution_expiration_date = fields.Datetime.now() + timedelta(days=days_to_add) if days_to_add > 0 else False

    @api.onchange('product_id', 'product_qty', 'product_uom_id')
    def _onchange_amunet_product_setup(self):
        if not self.product_id:
            return
            
        product = self.product_id

        # Leer la receta (BoM) para encontrar todos los reactivos y verificar su inventario vs la cantidad a producir
        warnings = []
        bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', product.product_tmpl_id.id), '|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)], limit=1)
        if bom:
            if not self._origin.id and self.product_qty == bom.product_qty:
                return

            # Conversion nativa UoM
            if self.product_uom_id and bom.product_uom_id:
                production_qty_bom_uom = self.product_uom_id._compute_quantity(self.product_qty or 1.0, bom.product_uom_id)
            else:
                production_qty_bom_uom = self.product_qty or 1.0
                
            bom_factor = production_qty_bom_uom / bom.product_qty if bom.product_qty else 1.0
            
            for line in bom.bom_line_ids:
                comp = line.product_id
                required_qty = line.product_qty * bom_factor
                
                # Odoo guarda los productos en su unidad base (ej. Unidades), pero la Lista pide otra unidad (ej. gramos)
                # Siempre se debe convertir el stock existente a la unidad que pide la receta para hacer algebra limpia:
                if comp.uom_id and line.product_uom_id and comp.uom_id != line.product_uom_id:
                    try:
                        available_qty = comp.uom_id._compute_quantity(comp.qty_available, line.product_uom_id)
                    except:
                        available_qty = comp.qty_available
                else:
                    available_qty = comp.qty_available
                
                if available_qty < required_qty:
                    missing_qty = required_qty - available_qty
                    # Diferenciar entre solucion hija y reactivo normal
                    if comp.categ_id and 'Solucion' in comp.categ_id.name:
                        warnings.append(f"CRITICO - Solucion Faltante: '{comp.name}'. Se requiere: {round(required_qty, 3)} pero solo hay: {round(available_qty, 3)} {line.product_uom_id.name}.")
                    else:
                        warnings.append(f"REACTIVO FALTANTE: '{comp.name}'. Falta comprar/surtir: {round(missing_qty, 3)} {line.product_uom_id.name}.")

        if warnings:
            return {
                'warning': {
                    'title': 'Analisis de Disponibilidad de Inventario',
                    'message': '\n'.join(warnings)
                }
            }

    @api.depends('move_raw_ids.amunet_is_valid')
    def _compute_all_ingredients_valid(self):
        for record in self:
            if not record.move_raw_ids:
                record.amunet_all_ingredients_valid = False
            else:
                record.amunet_all_ingredients_valid = all(move.amunet_is_valid for move in record.move_raw_ids)

    @api.depends('date_start')
    def _compute_scheduled_date_display(self):
        import pytz
        for rec in self:
            if rec.date_start:
                user_tz = self.env.user.tz or 'UTC'
                utc_dt = rec.date_start.replace(tzinfo=pytz.utc)
                local_dt = utc_dt.astimezone(pytz.timezone(user_tz))
                rec.amunet_scheduled_date_display = local_dt.strftime('%d.%m.%y')
            else:
                rec.amunet_scheduled_date_display = ''

    def _inverse_scheduled_date_display(self):
        import pytz
        from datetime import datetime
        for rec in self:
            val = (rec.amunet_scheduled_date_display or '').strip()
            if not val:
                continue
            try:
                user_tz = self.env.user.tz or 'UTC'
                tz = pytz.timezone(user_tz)
                new_date = datetime.strptime(val, '%d.%m.%y').date()
                # No reescribir date_start si la fecha mostrada NO cambio.
                # El display solo trae fecha (sin hora); reconstruir a
                # medianoche cambiaria date_start en cada guardado y
                # dispararia el candado de "informacion general" (y el
                # error nativo de desplanificar). Al guardar poniendo
                # lotes, la fecha no cambia -> aqui salimos sin tocar nada.
                if rec.date_start:
                    orig_local = rec.date_start.replace(
                        tzinfo=pytz.utc).astimezone(tz)
                    if orig_local.date() == new_date:
                        continue
                    # La fecha SI cambio (Mery la edito): conservar la
                    # hora original en vez de mandarla a medianoche.
                    local_dt = tz.localize(
                        datetime.combine(new_date, orig_local.time()))
                else:
                    local_dt = tz.localize(
                        datetime.combine(new_date, datetime.min.time()))
                rec.date_start = local_dt.astimezone(pytz.utc).replace(tzinfo=None)
            except ValueError:
                pass

    def _auto_generate_lot_draft(self, force_recreate=False):
        """Pre-visualiza el nombre del lote en draft SIN crearlo en BD.

        Politica Amunet: lote = folio del MO. Aqui solo previsualizamos
        ese nombre para que el supervisor lo vea antes de confirmar.
        """
        for prod in self:
            if prod.state != 'draft':
                continue
            # NUNCA reservamos/creamos lote fisico en draft para evitar lotes fantasma
            prod.lot_producing_ids = [Command.clear()]
            if prod.product_id and prod.product_id.tracking != 'none':
                prod.solution_lot_id = prod.name or 'Auto-Lote'
            else:
                prod.solution_lot_id = ''

    def _amunet_complete_workorder_workcenters(self, vals):
        """Completa work centers cuando la UI manda work orders parciales."""
        commands = vals.get('workorder_ids') or []
        if not commands:
            return

        bom = self.env['mrp.bom']
        if vals.get('bom_id'):
            bom = self.env['mrp.bom'].browse(vals['bom_id']).exists()

        operations_by_name = {}
        if bom:
            operations_by_name = {
                operation.name: operation
                for operation in bom.operation_ids
                if operation.name
            }

        cleaned_commands = []
        changed = False

        for command in commands:
            if not (
                isinstance(command, (list, tuple))
                and len(command) >= 3
                and command[0] == 0
                and isinstance(command[2], dict)
            ):
                cleaned_commands.append(command)
                continue

            workorder_vals = command[2]
            if not workorder_vals and bom:
                # The web client can send empty virtual work orders when the
                # field is invisible. Dropping them lets MRP rebuild the real
                # work orders from the BoM operations.
                changed = True
                continue

            if workorder_vals.get('workcenter_id'):
                cleaned_commands.append(command)
                continue

            operation = self.env['mrp.routing.workcenter']
            operation_id = workorder_vals.get('operation_id')
            if isinstance(operation_id, int):
                operation = self.env['mrp.routing.workcenter'].browse(operation_id).exists()

            if not operation and workorder_vals.get('name'):
                operation = operations_by_name.get(workorder_vals['name'], operation)

            if operation and operation.workcenter_id:
                workorder_vals['workcenter_id'] = operation.workcenter_id.id

            cleaned_commands.append(command)

        if changed:
            if cleaned_commands:
                vals['workorder_ids'] = cleaned_commands
            else:
                vals.pop('workorder_ids', None)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # This is a product master-data flag exposed as a related field.
            # During MO creation, the web client sends the displayed value back;
            # production users must not write product configuration.
            vals.pop('amunet_sys_req_qc', None)
            if vals.get('product_id') and not vals.get('quality_analysis_status'):
                product = self.env['product.product'].browse(vals['product_id']).exists()
                if product and (product.amunet_req_quality_control or product.qc_required):
                    vals['quality_analysis_status'] = 'to_request'
            self._amunet_complete_workorder_workcenters(vals)
            # Folio Amunet de la MO: si el producto tiene
            # mo_sequence_id (formato MMAA/NN/ABR), usar esa
            # secuencia en lugar de la generica del picking_type.
            # Asi una MO de VIH 1.2 queda con folio "0526/01/VIH".
            if vals.get('product_id') and (
                not vals.get('name') or vals.get('name') == '/'
            ):
                product = self.env['product.product'].browse(
                    vals['product_id']).exists()
                mo_seq = product and product.product_tmpl_id.mo_sequence_id
                if mo_seq:
                    vals['name'] = mo_seq.next_by_id()
        productions = super().create(vals_list)
        # Forzar recompute de los campos de calidad/caducidad. El
        # compute @api.depends('product_id','date_start') a veces no
        # se dispara con cache fresco en create. Esto garantiza que
        # amunet_expiration_text y solution_expiration_date queden
        # poblados desde el inicio.
        productions._compute_quality_params()
        productions._auto_generate_lot_draft()
        return productions

    # Campos de "informacion general" de la orden que NO se pueden
    # modificar una vez planificada (confirmada en adelante), salvo Mery.
    _AMUNET_GENERAL_INFO_FIELDS = (
        'product_id', 'product_qty', 'bom_id', 'user_id',
        'date_start', 'amunet_scheduled_date_display', 'amunet_expiration_text',
    )

    # Flag de UI: True si el usuario actual es Mery (unica excepcion para
    # modificar la informacion general de una orden ya planificada).
    amunet_user_is_mery = fields.Boolean(
        string='Es Mery', compute='_compute_amunet_user_is_mery')

    @api.depends_context('uid')
    def _compute_amunet_user_is_mery(self):
        is_mery = self.env.user.login == 'desarrollo@amunet.com.mx'
        for rec in self:
            rec.amunet_user_is_mery = is_mery

    def _amunet_field_value_changed(self, field_name, new_value):
        field = self._fields[field_name]
        old = self[field_name]
        if field.type == 'many2one':
            return (old.id or False) != (new_value or False)
        if field.type == 'date':
            return str(old or '') != str(new_value or '')
        if field.type == 'datetime':
            # Lo unico que el usuario edita del calendario es la FECHA (el
            # campo visible 'Fecha Programada' es solo fecha, sin hora). El
            # formulario (sobre todo en movil) reenvia date_start con la hora
            # truncada a medianoche; eso NO es un cambio real. Comparamos
            # solo la FECHA en la zona horaria del usuario para no bloquear
            # a Almacen al surtir lotes en una orden ya planificada.
            import pytz
            tz = pytz.timezone(self.env.user.tz or 'UTC')

            def _local_date(v):
                dt = fields.Datetime.to_datetime(v)
                if not dt:
                    return False
                return dt.replace(tzinfo=pytz.utc).astimezone(tz).date()
            return _local_date(old) != _local_date(new_value)
        return old != new_value

    def _amunet_check_general_info_lock(self, vals):
        # Solo aplica a escrituras manuales; se omite en flujos internos.
        if self.env.su or self.env.context.get('amunet_supply_internal'):
            return
        # Excepcion: Mery puede modificar la informacion general siempre.
        if self.env.user.login == 'desarrollo@amunet.com.mx':
            return
        touched = [f for f in self._AMUNET_GENERAL_INFO_FIELDS if f in vals]
        if not touched:
            return
        for mo in self:
            if mo.state == 'draft':
                continue
            for f in touched:
                if mo._amunet_field_value_changed(f, vals[f]):
                    raise UserError(_(
                        'La orden %(mo)s ya esta planificada. Solo Mery puede '
                        'modificar la informacion general (campo: %(f)s).'
                    ) % {'mo': mo.name, 'f': mo._fields[f].string})

    def write(self, vals):
        self._amunet_check_general_info_lock(vals)
        res = super().write(vals)
        if 'product_id' in vals:
            # Si cambia el producto en borrador, forzamos regenerar la previsualizacion
            for prod in self.filtered(lambda p: p.state == 'draft'):
                prod._auto_generate_lot_draft(force_recreate=True)
                
        # Sincronización robusta: Si el lote real cambia (por ej. Limpiar o Generar serial), actualiza el campo texto
        if 'lot_producing_ids' in vals or 'lot_producing_id' in vals:
            for prod in self:
                if prod.lot_producing_ids:
                    prod.solution_lot_id = ", ".join(prod.lot_producing_ids.mapped('name'))
                    
        return res

    def _amunet_check_lote_lock(self):
        # El 'Lote producido' es info general: no se cambia (Limpiar /
        # Generar serial) una vez planificada la orden, salvo Mery.
        if self.env.su or self.env.user.login == 'desarrollo@amunet.com.mx':
            return
        for mo in self:
            if mo.state != 'draft':
                raise UserError(_(
                    'La orden %s ya esta planificada. Solo Mery puede '
                    'modificar el Lote producido.') % mo.name)

    def action_generate_serial(self):
        self._amunet_check_lote_lock()
        # Asegurar sincronizacion al darle al botón nativo de Odoo "Generar Lote"
        res = super().action_generate_serial()
        for prod in self:
            if prod.lot_producing_ids:
                prod.solution_lot_id = ", ".join(prod.lot_producing_ids.mapped('name'))
        return res
        
    def action_clear_lot_producing_ids(self):
        self._amunet_check_lote_lock()
        res = super().action_clear_lot_producing_ids()
        for prod in self:
            if not prod.lot_producing_ids:
                prod.solution_lot_id = "Pendiente de Lote"
        return res

    @api.onchange('product_id')
    def _onchange_product_id_lot_predict(self):
        """Permite que la UI muestre la previsualizacion en vivo al cambiar producto antes de guardar"""
        self._auto_generate_lot_draft()

    def button_plan(self):
        # Politica Amunet (mejora 2026-07-02): NO bloquear la planeacion por
        # falta de material. Planear != consumir: solo programa actividades.
        # Se permite planear y, si falta material en Fabrica, se avisa a
        # Almacen (actividad) para que lo traslade desde otro almacen (ej.
        # Burgos) y se advierte al planificador del posible retraso en el
        # historial de la orden. El candado real de material se mantiene en
        # el flujo de Surtir/Producir (no se produce sin material).
        for mo in self.filtered(lambda m: not m.is_planned):
            sin_material = mo.move_raw_ids.filtered(
                lambda m: m.state not in ('assigned', 'done', 'cancel')
            )
            if sin_material:
                mo._amunet_notify_plan_material_shortage(sin_material)
        return super().button_plan()

    def _amunet_notify_plan_material_shortage(self, short_moves):
        """Al planificar con material incompleto: crea actividad a Almacen para
        trasladar el faltante desde otro almacen a Fabrica (o escalar a compras
        si no hay en ningun lado) y deja un mensaje al planificador en el
        historial de la orden. NO bloquea la planeacion."""
        self.ensure_one()
        Quant = self.env['stock.quant'].sudo()
        Loc = self.env['stock.location'].sudo()
        lineas_planif = []
        lineas_almacen = []
        for m in short_moves:
            falta = (m.product_uom_qty or 0.0) - (m.quantity or 0.0)
            if falta <= 0:
                continue
            origen = m.location_id
            origen_ids = Loc.search([('id', 'child_of', origen.id)]).ids
            otros = Quant.search([
                ('product_id', '=', m.product_id.id),
                ('location_id.usage', '=', 'internal'),
                ('location_id', 'not in', origen_ids),
            ])
            disp = {}
            for q in otros:
                libre = (q.quantity or 0.0) - (q.reserved_quantity or 0.0)
                if libre > 0:
                    disp[q.location_id] = disp.get(q.location_id, 0.0) + libre
            pname = m.product_id.display_name
            uom = m.product_uom.name or ''
            if disp:
                fuentes = ', '.join('%s (%.0f)' % (loc.complete_name, v)
                                    for loc, v in disp.items())
                lineas_almacen.append(
                    '- %s: TRASLADAR %.2f %s a %s. Disponible en: %s'
                    % (pname, falta, uom, origen.complete_name, fuentes))
                lineas_planif.append(
                    '- %s: faltan %.2f %s en Fabrica (hay en %s -> requiere traslado)'
                    % (pname, falta, uom, fuentes))
            else:
                lineas_almacen.append(
                    '- %s: faltan %.2f %s y NO hay en otro almacen -> ESCALAR A COMPRAS'
                    % (pname, falta, uom))
                lineas_planif.append(
                    '- %s: faltan %.2f %s (sin stock en ningun almacen -> requiere compra)'
                    % (pname, falta, uom))
        if not lineas_almacen:
            return
        # 1) Mensaje al planificador (historial de la orden)
        self.sudo().message_post(body=Markup(
            '<b>Orden planificada con material INCOMPLETO.</b> Puede retrasar la '
            'entrega. Se avisó a Almacén para el traslado:<br/>%s'
            % '<br/>'.join(lineas_planif)))
        # 2) Actividad a Almacen (traslado del material)
        wh_group = self.env.ref(
            'amunet_material_request.group_material_warehouse',
            raise_if_not_found=False)
        if not wh_group:
            return
        users = wh_group.sudo().all_user_ids.filtered(
            lambda u: u.active and u.id != 1)
        note = Markup(
            'Falta material para la orden <b>%s</b> (ya planificada). Traslada '
            'de otro almacén a Fábrica antes de surtir:<br/>%s'
            % (self.name, '<br/>'.join(lineas_almacen)))
        for u in users:
            self.sudo().activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('Trasladar material para %s') % self.name,
                note=note, user_id=u.id)

    def action_confirm(self):
        # Crear fisicamente el lote ahora que se esta confirmando.
        # Politica Amunet: el lote del producto terminado tiene EL MISMO
        # nombre que el folio de la MO (ej. MO 0526/04/IGE -> lote
        # 0526/04/IGE). Un solo identificador por batch para
        # trazabilidad simplificada (ISO 13485 / Cofepris).
        for prod in self:
            if prod.state == 'draft' and prod.product_id and prod.product_id.tracking != 'none' and not prod.lot_producing_ids:
                try:
                    lot_vals = {
                        'name': prod.name,
                        'product_id': prod.product_id.id,
                        'company_id': prod.company_id.id,
                    }
                    prod.lot_producing_ids = [Command.create(lot_vals)]
                    prod.solution_lot_id = prod.name
                except Exception:
                    pass
        res = super().action_confirm()
        # Notificar a almacen que hay una MO pendiente de surtir.
        # Reutiliza el patron de amunet_material_request._notify_warehouse_pending.
        for prod in self:
            prod._amunet_notify_warehouse_pending_supply()
        return res

    def _amunet_notify_warehouse_pending_supply(self):
        """Crea actividades para los almacenistas avisando que hay una
        MO pendiente de surtir. Espeja el patron de
        amunet_material_request._notify_warehouse_pending (lineas 379-420).

        Una actividad por cada usuario activo del grupo
        amunet_material_request.group_material_warehouse. Se eliminan
        cuando almacen toma el surtido (en
        action_amunet_start_supply de mrp.workorder).
        """
        self.ensure_one()
        wh_group = self.env.ref(
            'amunet_material_request.group_material_warehouse',
            raise_if_not_found=False,
        )
        todo_act = self.env.ref(
            'mail.mail_activity_data_todo', raise_if_not_found=False)
        if not wh_group or not todo_act:
            return
        users = wh_group.sudo().all_user_ids.filtered(
            lambda u: u.active and u.id != 1)
        if not users:
            return
        # Construir link al menu Inventario -> Operaciones -> Surtido
        # de produccion para que el almacenista entre por su modulo
        # natural, no por Produccion.
        action = self.env.ref(
            'amunet_production.action_amunet_warehouse_supply_workorders',
            raise_if_not_found=False,
        )
        link_html = ''
        if action:
            link_html = (
                '<br/><br/><a href="/odoo/action-%s" class="btn btn-primary">'
                'Abrir surtido en Inventario</a>'
            ) % action.id
        body = _(
            'Producto: %(p)s\nCantidad: %(q)s %(u)s\nComponentes: %(n)s\nOrigen: %(o)s'
        ) % {
            'p': self.product_id.display_name,
            'q': self.product_qty,
            'u': self.product_uom_id.name or '',
            'n': len(self.move_raw_ids),
            'o': self.origin or '-',
        }
        note_html = body.replace('\n', '<br/>') + link_html
        for u in users:
            self.sudo().activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('Surtir produccion %s') % self.name,
                note=note_html,
                user_id=u.id,
            )

    def _amunet_close_warehouse_supply_activities(self):
        """Elimina las actividades de surtido pendientes (cuando alguien
        ya tomo el surtido o se completo). Identifica solo las que
        creamos por el prefijo del summary.
        """
        self.ensure_one()
        prefix = _('Surtir produccion ')
        acts = self.sudo().activity_ids.filtered(
            lambda a: a.summary and a.summary.startswith(prefix)
        )
        acts.unlink()

    def _amunet_notify_production_supply_ready(self):
        """Avisa al supervisor de produccion que el almacen confirmo el
        surtido y esta pendiente de validacion. Patron espejo de
        amunet_material_request._notify_requester_ready.
        """
        self.ensure_one()
        prod_group = self.env.ref(
            'amunet_production.group_production_supervisor',
            raise_if_not_found=False,
        )
        todo_act = self.env.ref(
            'mail.mail_activity_data_todo', raise_if_not_found=False)
        if not prod_group or not todo_act:
            return
        users = prod_group.sudo().all_user_ids.filtered(
            lambda u: u.active and u.id != 1)
        if not users:
            return
        body = _(
            'Almacen confirmo el surtido y espera tu validacion.\n'
            'MO: %(m)s\nProducto: %(p)s\nSurtido por: %(u)s'
        ) % {
            'm': self.name,
            'p': self.product_id.display_name,
            'u': self.env.user.display_name,
        }
        for u in users:
            self.sudo().activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('Validar surtido %s') % self.name,
                note=body.replace('\n', '<br/>'),
                user_id=u.id,
            )
        # Aviso EXPLICITO al responsable de la orden (user_id) de que
        # almacen ya termino el surtido: actividad si no la tiene ya, y
        # mensaje en el chatter que le llega a su bandeja de Discuss.
        responsable = self.user_id
        if responsable and responsable.active and responsable.id != 1:
            if responsable not in users:
                self.sudo().activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_('Validar surtido %s') % self.name,
                    note=body.replace('\n', '<br/>'),
                    user_id=responsable.id,
                )
            self.sudo().message_post(
                body=_(
                    'Almacen termino el surtido de los materiales de esta '
                    'orden (surtido por %(u)s). Responsable: %(r)s, queda '
                    'pendiente de recepcion/validacion.'
                ) % {'u': self.env.user.display_name, 'r': responsable.name},
                partner_ids=responsable.partner_id.ids,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )

    def _amunet_close_production_supply_activities(self):
        self.ensure_one()
        prefix = _('Validar surtido ')
        acts = self.sudo().activity_ids.filtered(
            lambda a: a.summary and a.summary.startswith(prefix)
        )
        acts.unlink()

    def _get_move_raw_values(self, product, product_uom_qty, product_uom, operation_id=False, bom_line=False):
        """Override Amunet:
        Redondea HACIA ARRIBA la cantidad de componentes cuando el
        producto se mide en unidades enteras (no admite fracciones).
        Caso real: VIH tiene 0.1 viales por unidad; para fabricar 75
        kits hacen falta 7.5 viales -> se piden 8 (no se puede pedir
        medio vial al almacen).
        Se aplica solo cuando la UoM del COMPONENTE es 'Unidades'
        (uom.product_uom_unit). Para componentes en cm, ml, kg, etc.
        se respeta el decimal.
        """
        import math
        if product and product_uom_qty and not isinstance(product, dict):
            unit_uom = self.env.ref(
                'uom.product_uom_unit', raise_if_not_found=False)
            uom = product_uom or product.uom_id
            if unit_uom and uom and uom.id == unit_uom.id:
                product_uom_qty = math.ceil(product_uom_qty)
        return super()._get_move_raw_values(
            product, product_uom_qty, product_uom,
            operation_id=operation_id, bom_line=bom_line,
        )

    def _prepare_stock_lot_values(self):
        """Override Amunet:
        Si el producto tiene mo_sequence_id (formato Amunet), el lote
        del producto fabricado HEREDA el folio de la MO en lugar de
        consumir una secuencia distinta. Asi: MO=0526/01/VIH y el
        stock.lot del kit fabricado tambien sera 0526/01/VIH.
        """
        self.ensure_one()
        if self.product_id.product_tmpl_id.mo_sequence_id and self.name:
            return {
                'product_id': self.product_id.id,
                'company_id': self.company_id.id,
                'name': self.name,
            }
        return super()._prepare_stock_lot_values()

    def action_request_analysis(self):
        """Valida estado/reactivos/checklist y abre el Wizard de análisis"""
        self.ensure_one()

        if self.quality_analysis_status not in ('none', 'to_request', 'rejected'):
            raise UserError('El análisis de calidad ya fue solicitado o se encuentra aprobado.')

        # Validar que todos los reactivos tengan cantidad utilizada
        sin_cantidad = self.move_raw_ids.filtered(lambda m: not m.quantity or m.quantity <= 0)
        if sin_cantidad:
            nombres = ', '.join(sin_cantidad.mapped('product_id.name'))
            raise UserError(f'Los siguientes reactivos no tienen Cantidad Utilizada registrada:\n{nombres}\n\nIngresa el valor antes de confirmar el análisis.')

        if not self.amunet_all_ingredients_valid:
            raise UserError('Todos los reactivos deben estar marcados como Válidos para proceder.')

        # Validar checklist operativa: bitacoras, calculos, dilucion y
        # aforar son requisitos del flujo de SOLUCIONES (preparacion
        # quimica). Para kits y otros productos no aplican porque no
        # hay preparacion de mezclas.
        if self.amunet_is_solution_product:
            missing = []
            if self.amunet_sys_req_history and not self.amunet_check_history_log:
                missing.append("Registro en Bitácoras")
            if self.amunet_sys_req_calc and not self.amunet_check_calculations:
                missing.append("Cálculos Realizados")
            if self.amunet_sys_req_dilution and not self.amunet_check_dilution:
                missing.append("Dilución de Reactivos")
            if self.amunet_sys_req_aforar and not self.amunet_check_aforar:
                missing.append("Aforar")
            if missing:
                raise UserError('Completa las siguientes actividades operativas antes de solicitar el análisis:\n- ' + '\n- '.join(missing))

        return {
            'name': 'Confirmar Solicitud de Análisis',
            'type': 'ir.actions.act_window',
            'res_model': 'amunet.production.analysis.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_production_id': self.id,
            }
        }
    
    def button_mark_done(self):
        """Bloqueo del flujo nativo de la orden de producción"""
        for record in self:
            # 0. Conciliación de materiales obligatoria si hay surtido registrado
            moves_with_supply = record.move_raw_ids.filtered(
                lambda m: m.state != 'cancel' and (m.amunet_qty_supplied or 0) > 0
            )
            if moves_with_supply and record.reconciliation_state != 'completed':
                estado = dict(record._fields['reconciliation_state'].selection).get(
                    record.reconciliation_state, record.reconciliation_state)
                raise UserError(_(
                    'Debe completar la conciliación de materiales antes de producir.\n'
                    'Estado actual: %s'
                ) % estado)

            # 1. Validar cantidades utilizadas en reactivos
            sin_cantidad = record.move_raw_ids.filtered(lambda m: not m.quantity or m.quantity <= 0)
            if sin_cantidad:
                nombres = ', '.join(sin_cantidad.mapped('product_id.name'))
                raise UserError(f'ATENCIÓN: Los siguientes reactivos no tienen Cantidad Utilizada:\n{nombres}\n\nCompleta los valores antes de marcar como hecho.')

            # 2. Validar Checklist Operativa
            missing = []
            if record.amunet_sys_req_history and not record.amunet_check_history_log: missing.append("Registro en Bitácoras")
            if record.amunet_sys_req_calc and not record.amunet_check_calculations: missing.append("Cálculos Realizados")
            if record.amunet_sys_req_dilution and not record.amunet_check_dilution: missing.append("Dilución de Reactivos")
            if record.amunet_sys_req_aforar and not record.amunet_check_aforar: missing.append("Aforar")
            if missing:
                raise UserError('ATENCIÓN: Faltan las siguientes actividades operativas por marcar en la Pestaña de Actividades:\n- ' + '\n- '.join(missing))
            
            # 2. Validar Calidad (solo si el producto lo requiere)
            if record.amunet_sys_req_qc and record.quality_analysis_status != 'approved':
                raise UserError('ATENCIÓN: Este producto requiere Análisis C.C. No puedes "Marcar como Hecho" hasta que el área de Calidad apruebe el análisis.')
                
        return super(MrpProduction, self).button_mark_done()
