# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError, ValidationError
from markupsafe import Markup

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _get_consumption_issues(self):
        """Ajuste amunet: el aviso nativo 'consumio una cantidad diferente' calcula
        el 'Por consumir' SOLO desde el BoM. Por eso los componentes del PLAN DE
        EMPAQUE (caja, funda, etc. -> moves sin bom_line) salian con esperado 0 aunque
        Almacen si los surte y se consumen. Aqui, para esas lineas, se toma la
        cantidad planificada del propio movimiento (should_consume_qty, que ya
        contempla el plan de empaque y es lo que muestra la tabla de ingredientes)
        en vez de 0. Si esa cantidad coincide con lo consumido, la linea deja de avisar.
        NO cambia cantidades reales ni la conciliacion; solo lo que muestra el aviso.
        """
        issues = super()._get_consumption_issues()
        if not issues:
            return issues
        adjusted = []
        for issue in issues:
            order, product, consumed, expected = issue
            # Solo se corrigen las lineas con esperado 0 que correspondan a un
            # movimiento de empaque (sin linea de BoM). El resto se deja igual.
            if not product.uom_id.is_zero(expected):
                adjusted.append(issue)
                continue
            pkg_moves = order.move_raw_ids.filtered(
                lambda m: m.product_id == product and not m.bom_line_id)
            if not pkg_moves:
                adjusted.append(issue)
                continue
            exp = sum(pkg_moves.mapped('should_consume_qty'))
            if product.uom_id.is_zero(exp):
                exp = sum(pkg_moves.mapped('product_uom_qty'))
            if product.uom_id.compare(exp, consumed) == 0:
                # El esperado del plan de empaque coincide con lo consumido: sin aviso.
                continue
            adjusted.append((order, product, consumed, exp))
        return adjusted

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
    amunet_all_dissolved = fields.Boolean(
        string='Reactivos disueltos',
        compute='_compute_amunet_all_dissolved',
        help='Verdadero cuando TODOS los reactivos de la orden estan marcados '
             'como disueltos. El pH final solo se puede capturar cuando esto es '
             'verdadero.')

    @api.depends('move_raw_ids.amunet_dissolution', 'move_raw_ids.state',
                 'move_raw_ids.product_id.categ_id')
    def _compute_amunet_all_dissolved(self):
        for rec in self:
            # El agua (solvente) no se disuelve: se excluye del candado.
            moves = rec.move_raw_ids.filtered(
                lambda m: m.state != 'cancel' and not m._amunet_is_water_solvent())
            rec.amunet_all_dissolved = bool(moves) and all(
                m.amunet_dissolution for m in moves)

    amunet_has_surtido_components = fields.Boolean(
        string='Tiene componentes de surtido',
        compute='_compute_amunet_has_surtido_components',
        help='Solo soluciones: True si algun componente es sub-solucion (requiere '
             'surtido). Controla si se muestra la columna Cantidad surtida.')

    @api.depends('move_raw_ids.amunet_needs_surtido')
    def _compute_amunet_has_surtido_components(self):
        for rec in self:
            rec.amunet_has_surtido_components = any(
                rec.move_raw_ids.mapped('amunet_needs_surtido'))
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

    # Piezas realmente fabricadas con las que se solicitó el análisis de PT.
    # Se captura en el wizard de solicitud y es la cantidad que se produce al
    # cerrar la orden. Sirve para que Calidad sepa cuántas piezas cubre el
    # análisis que aprueba o rechaza.
    amunet_pt_qty_solicitada = fields.Float(
        string='Piezas fabricadas (análisis)', readonly=True, copy=False, tracking=True)
    amunet_pt_qc_por_id = fields.Many2one(
        'res.users', string='Análisis PT resuelto por', readonly=True, copy=False)
    amunet_pt_qc_fecha = fields.Datetime(
        string='Fecha resolución análisis PT', readonly=True, copy=False)

    # ── Supervisión de elaboración (soluciones) ─────────────────────────────
    # Al terminar de elaborar la solucion, el fabricante la envia a supervision
    # de su JEFE DIRECTO (manager de RRHH), que firma con PIN. Sin esa firma no
    # se puede solicitar analisis (Flujo A) ni producir (Flujo B).
    amunet_supervision_state = fields.Selection([
        ('none', 'Sin enviar'),
        ('requested', 'Enviada a supervisión'),
        ('done', 'Supervisada'),
    ], string='Supervisión de elaboración', default='none', copy=False, tracking=True)
    amunet_supervisor_id = fields.Many2one(
        'res.users', string='Jefe que supervisa', readonly=True, copy=False)
    amunet_supervised_by_id = fields.Many2one(
        'res.users', string='Supervisado por', readonly=True, copy=False)
    amunet_supervised_date = fields.Datetime(
        string='Fecha de supervisión', readonly=True, copy=False)
    amunet_is_supervisor = fields.Boolean(
        string='Es supervisor actual', compute='_compute_amunet_is_supervisor')

    @api.depends('amunet_supervisor_id')
    def _compute_amunet_is_supervisor(self):
        for mo in self:
            mo.amunet_is_supervisor = bool(
                mo.amunet_supervisor_id and mo.amunet_supervisor_id == self.env.user)

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
    amunet_es_desarrollo = fields.Boolean(
        string='Es desarrollo',
        copy=False,
        help='Solucion de DESARROLLO: sin receta justa (cantidades ajustables), '
             'sin analisis de Calidad; el terminado entra a ARU/Desarrollo '
             '(segregado del stock de produccion). Requiere la supervision del '
             'jefe directo antes de producir.')
    amunet_desarrollo_nombre = fields.Char(
        string='Nombre de desarrollo',
        copy=False,
        help='Nombre/etiqueta de esta solucion de desarrollo, SOLO para esta '
             'orden. No cambia el producto maestro; se registra como referencia '
             'del lote producido.')
    amunet_receta_base_id = fields.Many2one(
        'product.product',
        string='Tomar receta base de',
        copy=False,
        help='Solucion existente cuya receta (lista de materiales) se copia como '
             'BASE a esta orden de desarrollo, para partir de ahi y ajustar. No '
             'cambia el producto ni su BoM; solo llena los componentes de esta orden.')
    amunet_ph_final = fields.Float(
        string='pH final',
        copy=False,
        digits=(4, 2),
        help='pH final obtenido de la solucion, capturado por quien la fabrica.')

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
                    if mo.amunet_sys_req_qc and not mo.amunet_es_desarrollo and mo.quality_analysis_status != 'approved':
                        # El analisis de calidad va ANTES de la conciliacion de
                        # materiales (decision Fernando 2026-07-30).
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
                    elif has_supply and mo.reconciliation_state != 'completed':
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
        # Candado: la conciliacion NO puede iniciarse antes de que se haya
        # solicitado el analisis de producto terminado. Solo aplica a ordenes
        # que requieren analisis de calidad (no a desarrollo).
        if self.amunet_sys_req_qc and not self.amunet_es_desarrollo \
                and self.quality_analysis_status not in ('requested', 'approved', 'rejected'):
            raise UserError(_(
                'No se puede iniciar la conciliación antes de solicitar el '
                'análisis de producto terminado. Primero usa "Solicitar '
                'análisis".'))
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
        # Se permite cantidad utilizada = 0: el material se entrego pero NO se
        # uso, y se devuelve todo (el sobrante = lo surtido). Como al iniciar la
        # conciliacion se precarga qty_used = qty_supplied, un 0 es siempre una
        # captura deliberada del operador. Solo se bloquea un valor negativo.
        sin_uso = moves.filtered(lambda m: (m.amunet_qty_used or 0.0) < 0)
        if sin_uso:
            nombres = ', '.join(sin_uso.mapped('product_id.display_name'))
            raise UserError(_('La cantidad utilizada no puede ser negativa: %s') % nombres)
        # Actualizar quantity = qty_used (lo que Odoo consumirá al validar la MO)
        # y marcar 'picked' EN SINCRONÍA con la cantidad conciliada: si hay
        # consumo real (qty_used>0) el move debe quedar 'picked' para que el
        # nativo lo CONSUMA al cerrar. Sin esto, los insumos surtidos por este
        # flujo (goteros/viales/controles) quedaban picked=False y el nativo los
        # CANCELABA al cerrar (material usado SIN descontar del stock ni
        # trazabilidad) + el aviso de consumo los mostraba en 0. Deriva de la
        # conciliación (qty_used), NO la pisa.
        for move in moves:
            picked = (move.amunet_qty_used or 0.0) > 0.0
            move.sudo().write({
                'quantity': move.amunet_qty_used,
                'picked': picked,
            })
            open_lines = move.move_line_ids.filtered(
                lambda l: l.state not in ('done', 'cancel'))
            if open_lines:
                open_lines.write({'picked': picked})
        # La conciliación SIEMPRE queda en 'validated' esperando la
        # confirmación explícita (aunque no haya sobrante). Antes se
        # auto-completaba sin sobrante; ahora siempre hay un paso de
        # confirmación final (Almacén) para cerrar la conciliación.
        self.write({
            'reconciliation_state': 'validated',
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
            msg += _('<br/>Sin sobrante. Falta confirmar la conciliación.')
        self.message_post(body=msg)

    def action_complete_reconciliation(self):
        self.ensure_one()
        if self.reconciliation_state != 'validated':
            raise UserError(_('Solo se puede confirmar la conciliación cuando está validada.'))
        self.write({
            'reconciliation_state': 'completed',
            'reconciliation_completed_by': self.env.user.id,
            'reconciliation_completed_date': fields.Datetime.now(),
        })
        has_surplus = any(
            (m.amunet_qty_supplied or 0) - (m.amunet_qty_used or 0) > 0.001
            for m in self.move_raw_ids.filtered(lambda m: m.state != 'cancel')
        )
        if has_surplus:
            body = _('Devolución de material sobrante confirmada por almacén '
                     '(<b>%s</b>). Conciliación completada.') % self.env.user.name
        else:
            body = _('Conciliación confirmada por almacén (<b>%s</b>) — sin '
                     'sobrante que devolver. Conciliación completada.') % self.env.user.name
        self.message_post(body=body)
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
            if rec.amunet_sys_req_qc and not rec.amunet_es_desarrollo:
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

    def _amunet_apt_temporal_location(self):
        """Ubicacion 'Almacen Temporal PT' del almacen APT: es la cancha de
        Calidad del producto terminado (esperando analisis). Ahi produce la MO;
        al aprobar el analisis + validar la entrega, pasa a APT/Existencias."""
        return self.env['stock.location'].sudo().search([
            ('usage', '=', 'internal'),
            ('complete_name', 'like', 'APT/%Temporal%'),
        ], limit=1)

    @api.depends('picking_type_id', 'product_id')
    def _compute_locations(self):
        """Los PRODUCTOS TERMINADOS (pruebas rapidas + medios de cultivo) se
        producen hacia el 'Almacen Temporal PT' del APT (cancha de Calidad,
        esperando analisis), aunque su MO consuma insumos de AMP. Al aprobar
        el analisis y validar la entrega, pasan a APT/Existencias. Soluciones
        y demas se quedan donde el tipo de operacion los ponga (AMP).
        Decision de Mery 2026-08-13/14."""
        super()._compute_locations()
        temporal = self._amunet_apt_temporal_location()
        if not temporal:
            return
        for production in self:
            categ = ((production.product_id.categ_id.complete_name or '')
                     if production.product_id else '')
            if categ.startswith('Producto terminado'):
                production.location_dest_id = temporal.id

    @api.depends('product_id', 'date_start')
    def _amunet_compute_expiration(self, product, base_date):
        """Caducidad = base_date + duracion del producto RESPETANDO su unidad
        (dias/meses/años), con fecha dia-precisa. Default 24 meses si no hay
        duracion o no se puede parsear."""
        from dateutil.relativedelta import relativedelta
        txt = (product.amunet_expiration_text or '').lower()
        try:
            val = float(''.join(c for c in txt if c.isdigit() or c == '.'))
        except Exception:
            val = None
        if not val:
            return base_date + relativedelta(months=24)
        if 'año' in txt or 'ano' in txt:
            return base_date + relativedelta(months=int(round(val * 12)))
        if 'mes' in txt:
            return base_date + relativedelta(months=int(round(val)))
        if 'dia' in txt or 'día' in txt:
            return base_date + relativedelta(days=int(round(val)))
        return base_date + relativedelta(months=24)

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

            # Caducidad = fecha de FABRICACION (date_start) + duracion del
            # producto, RESPETANDO la unidad real (dias/meses/años), con fecha
            # dia-precisa. Antes se convertia todo a meses y los "N dias" (<30)
            # caian al default de 24 meses (bug). El texto de soluciones se
            # muestra en DD.MM.YY; el resto conserva YYYY-MM.
            base_date = rec.date_start or fields.Datetime.now()
            expiration = rec._amunet_compute_expiration(product, base_date)
            rec.solution_expiration_date = expiration
            if expiration:
                if rec.amunet_is_solution_product:
                    rec.amunet_expiration_text = expiration.strftime('%d.%m.%y')
                else:
                    rec.amunet_expiration_text = expiration.strftime('%Y-%m')
            else:
                rec.amunet_expiration_text = False

    @api.constrains('amunet_expiration_text')
    def _check_expiration_text_format(self):
        """Valida el formato al editar manualmente: soluciones DD.MM.YY
        (ej. 28.05.26); el resto YYYY-MM (ej. 2026-05)."""
        import re
        pat_sol = re.compile(r'^(0[1-9]|[12]\d|3[01])\.(0[1-9]|1[0-2])\.\d{2}$')
        pat_gen = re.compile(r'^\d{4}-(0[1-9]|1[0-2])$')
        for rec in self:
            if not rec.amunet_expiration_text:
                continue
            if rec.amunet_is_solution_product:
                if not pat_sol.match(rec.amunet_expiration_text):
                    from odoo.exceptions import ValidationError
                    raise ValidationError(_(
                        'El formato de caducidad de soluciones debe ser '
                        'DD.MM.YY (ejemplo: 28.05.26). Recibido: "%s"'
                    ) % rec.amunet_expiration_text)
            elif not pat_gen.match(rec.amunet_expiration_text):
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

        self.quality_ph_initial = product.amunet_initial_ph

        # Vista previa en vivo alineada al calculo almacenado (mismo helper):
        # caducidad = fecha de fabricacion + duracion, respetando la unidad.
        base_date = self.date_start or fields.Datetime.now()
        expiration = self._amunet_compute_expiration(product, base_date)
        self.solution_expiration_date = expiration
        if expiration:
            self.amunet_expiration_text = (
                expiration.strftime('%d.%m.%y') if self.amunet_is_solution_product
                else expiration.strftime('%Y-%m'))
        else:
            self.amunet_expiration_text = False

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

        Politica Amunet (PNOGE-014):
          - Producto TERMINADO: lote = folio del MO.
          - SOLUCIONES: lote = DDMMYY-NN (otra forma de lotificar). Aqui se
            previsualiza ese formato para que se vea que la solucion lleva
            un lote distinto al folio.
        """
        for prod in self:
            if prod.state != 'draft':
                continue
            # NUNCA reservamos/creamos lote fisico en draft para evitar lotes fantasma
            prod.lot_producing_ids = [Command.clear()]
            if prod.product_id and prod.product_id.tracking != 'none':
                if prod.amunet_is_solution_product:
                    prod.solution_lot_id = prod._amunet_next_solution_lot_name()
                else:
                    prod.solution_lot_id = prod.name or 'Auto-Lote'
            else:
                prod.solution_lot_id = ''

    @api.onchange('product_id', 'route_type')
    def _amunet_onchange_preview_lote_solucion(self):
        """Al elegir el producto o poner la linea = Soluciones, refresca en
        vivo la vista previa del lote para que muestre el formato correcto
        (DDMMYY-NN para soluciones, folio para lo demas)."""
        for prod in self:
            if prod.state and prod.state != 'draft':
                continue
            if not (prod.product_id and prod.product_id.tracking != 'none'):
                prod.solution_lot_id = ''
                continue
            if prod.amunet_is_solution_product:
                prod.solution_lot_id = prod._amunet_next_solution_lot_name()
            else:
                prod.solution_lot_id = prod.name or 'Auto-Lote'

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

    @api.onchange('product_id')
    def _amunet_onchange_product_desarrollo(self):
        # Al elegir un producto de desarrollo (STDES01), marcar la orden como
        # desarrollo para que aparezcan sus campos y se active la receta libre.
        if self.product_id and self.product_id.product_tmpl_id.amunet_es_desarrollo:
            self.amunet_es_desarrollo = True

    def action_amunet_cargar_receta_base(self):
        """Copia la receta (BoM) de la solucion base elegida a los componentes de
        esta orden de desarrollo, escalada a la cantidad de la orden. Es solo una
        BASE de partida: despues se editan/agregan/quitan componentes libremente.
        No cambia el producto ni su BoM."""
        self.ensure_one()
        if not self.amunet_es_desarrollo:
            raise UserError(_('Esta funcion es solo para soluciones de desarrollo.'))
        base = self.amunet_receta_base_id
        if not base:
            raise UserError(_('Elige en "Tomar receta base de" la solucion cuya '
                              'receta quieres copiar como base.'))
        bom = self.env['mrp.bom']._bom_find(base, company_id=self.company_id.id).get(base)
        if not bom or not bom.bom_line_ids:
            raise UserError(_('La solucion "%s" no tiene una receta (lista de '
                              'materiales) para copiar.') % base.display_name)
        factor = (self.product_qty / bom.product_qty) if bom.product_qty else 1.0
        # Limpiar los componentes actuales en borrador antes de cargar la base.
        self.move_raw_ids.filtered(lambda m: m.state == 'draft').unlink()
        vals_list = []
        for bl in bom.bom_line_ids:
            qty = bl.product_qty * factor
            vals = self._get_move_raw_values(
                bl.product_id, qty, bl.product_uom_id, bom_line=bl)
            vals_list.append((0, 0, vals))
        self.move_raw_ids = vals_list
        self.message_post(body=_(
            'Receta base copiada de %s (x%.4f de la cantidad). Ajusta los '
            'componentes segun el desarrollo.') % (base.display_name, factor))
        return True

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
            # Solucion de DESARROLLO: si el producto esta marcado como de
            # desarrollo, la orden hereda es_desarrollo automaticamente (receta
            # ajustable, sin analisis de Calidad, ARU/Desarrollo, con supervision).
            if vals.get('product_id') and 'amunet_es_desarrollo' not in vals:
                prod_dev = self.env['product.product'].browse(vals['product_id']).exists()
                if prod_dev and prod_dev.product_tmpl_id.amunet_es_desarrollo:
                    vals['amunet_es_desarrollo'] = True
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
                    vals['name'] = mo_seq._amunet_next_folio_mensual()
        productions = super().create(vals_list)
        # Forzar recompute de los campos de calidad/caducidad. El
        # compute @api.depends('product_id','date_start') a veces no
        # se dispara con cache fresco en create. Esto garantiza que
        # amunet_expiration_text y solution_expiration_date queden
        # poblados desde el inicio.
        productions._compute_quality_params()
        productions._auto_generate_lot_draft()
        # SOLUCIONES: el folio codificado DDMMYY-NN NO se asigna en borrador (asi
        # dos borradores del mismo dia no comparten folio ni chocan). El borrador
        # conserva su nombre generico; el folio codificado se asigna al CONFIRMAR
        # (ver action_confirm), donde ya es unico. PNOGE-014.
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
        # El formulario (sobre todo movil) reenvia date_start con la hora
        # truncada a medianoche al guardar. Si la FECHA no cambia, no es un
        # cambio real: lo descartamos ANTES de escribir para no disparar el
        # candado de informacion general NI el error nativo de Odoo
        # ("cannot unplan... work orders already started") al surtir lotes
        # en una orden ya planificada.
        if ('date_start' in vals and vals.get('date_start')
                and not self.env.su):
            import pytz
            tz = pytz.timezone(self.env.user.tz or 'UTC')
            new_dt = fields.Datetime.to_datetime(vals['date_start'])
            new_local = (new_dt.replace(tzinfo=pytz.utc).astimezone(tz).date()
                         if new_dt else False)

            def _same_date(rec):
                if not rec.date_start:
                    return False
                return rec.date_start.replace(
                    tzinfo=pytz.utc).astimezone(tz).date() == new_local

            if self and all(_same_date(rec) for rec in self):
                vals = dict(vals)
                vals.pop('date_start')
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
        # Candado anti-duplicacion (2026-07-16): "Planificar" es IDEMPOTENTE.
        # Ejecutarlo dos veces (doble clic o replanificacion) regeneraba las
        # ordenes de trabajo dejando juegos duplicados (caso MO 0726/02/R01:
        # 2 planeaciones con 2 min de diferencia -> 14 OT en vez de 7). Si la
        # orden YA esta planificada y ya tiene OT, se omite (no se regenera).
        ya_planificadas = self.filtered(
            lambda m: m.is_planned and m.workorder_ids)
        a_planificar = self - ya_planificadas
        if ya_planificadas:
            ya_planificadas.sudo().message_post(body=Markup(
                'Se omitió <b>Planificar</b>: la orden ya estaba planificada '
                'con órdenes de trabajo. No se regeneraron para evitar '
                'duplicados.'))
        if not a_planificar:
            return True
        # Politica Amunet (mejora 2026-07-02): NO bloquear la planeacion por
        # falta de material. Planear != consumir: solo programa actividades.
        # Se permite planear y, si falta material en Fabrica, se avisa a
        # Almacen (actividad) para que lo traslade desde otro almacen (ej.
        # Burgos) y se advierte al planificador del posible retraso en el
        # historial de la orden. El candado real de material se mantiene en
        # el flujo de Surtir/Producir (no se produce sin material).
        for mo in a_planificar.filtered(lambda m: not m.is_planned):
            sin_material = mo.move_raw_ids.filtered(
                lambda m: m.state not in ('assigned', 'done', 'cancel')
            )
            if sin_material:
                mo._amunet_notify_plan_material_shortage(sin_material)
        return super(MrpProduction, a_planificar).button_plan()

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

    def _amunet_next_solution_lot_name(self):
        """Numero de lote de SOLUCIONES segun PNOGE-014 'Asignacion de Numeros
        de Lote': formato DDMMYY-NN, donde DD/MM/YY = dia/mes/anio de
        elaboracion y NN = consecutivo de la solucion elaborada ese MISMO dia.
        El consecutivo se calcula contra los lotes existentes con ese prefijo
        para que sea unico e irrepetible."""
        self.ensure_one()
        fecha = fields.Date.context_today(self)
        prefix = fecha.strftime('%d%m%y')
        Lot = self.env['stock.lot'].sudo()
        patron = re.compile(r'^%s-(\d+)$' % prefix)
        consec = 0
        for lot in Lot.search([('name', '=like', prefix + '-%')]):
            m = patron.match(lot.name or '')
            if m:
                consec = max(consec, int(m.group(1)))
        return '%s-%02d' % (prefix, consec + 1)

    def action_confirm(self):
        # Crear fisicamente el lote ahora que se esta confirmando.
        # Politica Amunet (PNOGE-014):
        #  - Producto TERMINADO: el lote = folio de la MO (ej. 0526/04/IGE).
        #  - SOLUCIONES: el lote = DDMMYY-NN (dia de elaboracion + consecutivo),
        #    ver _amunet_next_solution_lot_name.
        # Un solo identificador por batch para trazabilidad (ISO 13485 / Cofepris).
        for prod in self:
            if prod.state == 'draft' and prod.product_id and prod.product_id.tracking != 'none' and not prod.lot_producing_ids:
                try:
                    lot_name = prod.name
                    if prod.amunet_is_solution_product:
                        lot_name = prod._amunet_next_solution_lot_name()
                    lot_vals = {
                        'name': lot_name,
                        'product_id': prod.product_id.id,
                        'company_id': prod.company_id.id,
                    }
                    # Soluciones de desarrollo: el nombre de desarrollo se guarda
                    # como referencia del lote (identifica el batch sin tocar el
                    # producto maestro).
                    if prod.amunet_es_desarrollo and prod.amunet_desarrollo_nombre:
                        lot_vals['ref'] = prod.amunet_desarrollo_nombre
                    prod.lot_producing_ids = [Command.create(lot_vals)]
                    prod.solution_lot_id = lot_name
                    # El folio de la solucion coincide con el lote codificado.
                    if prod.amunet_is_solution_product:
                        prod.name = lot_name
                except Exception:
                    pass
        res = super().action_confirm()
        # Ruteo del terminado de SOLUCIONES segun requieran analisis o no.
        self._amunet_route_solution_finished()
        # Surtido DENTRO de la orden solo si la solucion lleva sub-soluciones.
        self._amunet_create_solution_supply_workorder()
        # Notificar a almacen que hay una MO pendiente de surtir.
        # Reutiliza el patron de amunet_material_request._notify_warehouse_pending.
        for prod in self:
            prod._amunet_notify_warehouse_pending_supply()
        return res

    def _amunet_route_solution_finished(self):
        """Ruta del terminado de SOLUCIONES:
        - SIN analisis (amunet_req_quality_control=False): -> ARU/Stock, disponible
          para hacer/ajustar otras soluciones.
        - CON analisis: -> Control de calidad (custodia mientras Calidad analiza).
          Al aprobar, la maquinaria QC lo entrega a existencias validado por
          Almacen (recepcion) y merma el muestreo.
        - DESARROLLO (amunet_es_desarrollo): -> ARU/Desarrollo (segregado, sin
          analisis), sin importar el flag de QC del producto.
        Kits y otros productos no se tocan."""
        aru = self.env['stock.warehouse'].sudo().search([('code', '=', 'ARU')], limit=1)
        aru_stock = aru.lot_stock_id if aru else False
        qc_loc = self.env['stock.location'].sudo().search(
            [('complete_name', '=', 'AMP/Control de calidad')], limit=1)
        aru_dev = self.env['stock.location'].sudo().search(
            [('complete_name', '=', 'ARU/Desarrollo')], limit=1)
        for mo in self.filtered(lambda m: m.amunet_is_solution_product):
            if mo.amunet_es_desarrollo:
                dest = aru_dev
            else:
                req_qc = mo.product_id.product_tmpl_id.amunet_req_quality_control
                dest = qc_loc if req_qc else aru_stock
            if not dest:
                continue
            mo.location_dest_id = dest.id
            moves = mo.move_finished_ids.filtered(
                lambda mv: mv.state not in ('done', 'cancel'))
            if moves:
                moves.write({'location_dest_id': dest.id})

    def _amunet_create_solution_supply_workorder(self):
        """Surtido DENTRO de la orden de SOLUCION: solo cuando la solucion lleva
        componentes sub-solucion (needs_surtido=True, ej. una 'Solucion de
        trabajo' que Almacen tiene en existencia). Crea un workorder de Surtido
        (centro de trabajo AMP) para que Almacen la surta con Iniciar/Confirmar/
        Recibir. Los reactivos vienen de ARU y NO se surten aqui. Si la solucion
        no lleva sub-soluciones, no se crea nada."""
        amp = self.env['mrp.workcenter'].sudo().search([('code', '=', 'AMP')], limit=1)
        if not amp:
            return
        for mo in self.filtered(lambda m: m.amunet_is_solution_product):
            if mo.amunet_supply_workorder_id:
                continue
            needs = mo.move_raw_ids.filtered(
                lambda mv: mv.amunet_needs_surtido and mv.state != 'cancel')
            if not needs:
                continue
            self.env['mrp.workorder'].sudo().create({
                'name': _('Surtido de materiales - %s') % (mo.product_id.name or ''),
                'production_id': mo.id,
                'workcenter_id': amp.id,
            })

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

    # ── Supervisión de elaboración ──────────────────────────────────────────
    def _amunet_get_direct_manager_user(self):
        """Usuario del JEFE DIRECTO (manager de RRHH) de quien elabora la orden."""
        self.ensure_one()
        Emp = self.env['hr.employee'].sudo()
        emp = Emp.search([('user_id', '=', self.env.user.id)], limit=1)
        if not emp and self.create_uid:
            emp = Emp.search([('user_id', '=', self.create_uid.id)], limit=1)
        mgr = emp.parent_id if emp else False
        return mgr.user_id if (mgr and mgr.user_id) else False

    def action_amunet_request_supervision(self):
        """El fabricante envia la solucion elaborada a supervision de su jefe
        directo. Crea una actividad al jefe y deja la orden 'Enviada a
        supervision'. Sin la firma del jefe no se puede solicitar analisis ni
        producir."""
        self.ensure_one()
        if not self.amunet_is_solution_product:
            raise UserError(_('La supervisión de elaboración solo aplica a soluciones.'))
        if self.amunet_supervision_state == 'done':
            raise UserError(_('Esta orden ya fue supervisada.'))
        mgr = self._amunet_get_direct_manager_user()
        if not mgr:
            raise UserError(_(
                'No se encontró el jefe directo de quien elabora. '
                'Configura su Responsable en Recursos Humanos.'))
        self.sudo().write({'amunet_supervision_state': 'requested', 'amunet_supervisor_id': mgr.id})
        self.sudo().activity_schedule(
            'mail.mail_activity_data_todo', user_id=mgr.id,
            summary=_('Supervisar elaboración de solución %s') % self.name,
            note=_('Revisa la elaboración de la solución %s y firma la '
                   'supervisión (con PIN) antes de que continue.') % self.name)
        self.sudo().message_post(body=_('Enviada a supervisión de <b>%s</b>.') % mgr.name)
        return True

    def action_amunet_do_supervision(self):
        """El jefe directo abre la firma (PIN) para supervisar la elaboración."""
        self.ensure_one()
        if self.amunet_supervision_state != 'requested':
            raise UserError(_('No hay supervisión pendiente en esta orden.'))
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_amunet_supervision',
            _('Supervisión de elaboración'),
            _('Firma del jefe directo que supervisa la elaboración de %s.') % self.name)

    def _signature_amunet_supervision(self):
        self.ensure_one()
        self.sudo().write({
            'amunet_supervision_state': 'done',
            'amunet_supervised_by_id': self.env.user.id,
            'amunet_supervised_date': fields.Datetime.now(),
        })
        # Cerrar la actividad de supervision pendiente.
        acts = self.activity_ids.filtered(
            lambda a: a.user_id == self.amunet_supervisor_id)
        if acts:
            acts.sudo().action_feedback(feedback=_('Elaboración supervisada.'))
        self.sudo().message_post(
            body=_('Elaboración supervisada por <b>%s</b>.') % self.env.user.name)
        return True

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_amunet_supervision': _('Supervisión de elaboración'),
            '_amunet_qc_firma_aprobar': _('Aprobación de análisis de PT'),
            '_amunet_qc_firma_rechazar': _('Rechazo de análisis de PT'),
        }

    def _amunet_signature_required_procedures(self):
        # La supervision de elaboracion no exige capacitacion en SOPs al jefe.
        return self.env['amunet.quality.procedure']

    def action_request_analysis(self):
        """Valida estado/reactivos/checklist y abre el Wizard de análisis"""
        self.ensure_one()

        # Gate de supervisión: sin la firma del jefe directo no se solicita analisis.
        if self.amunet_is_solution_product and self.amunet_supervision_state != 'done':
            raise UserError(_(
                'Falta la SUPERVISIÓN del jefe directo antes de solicitar el '
                'análisis. Usa "Enviar a supervisión" y espera la firma del jefe.'))

        if self.quality_analysis_status not in ('none', 'to_request', 'rejected'):
            raise UserError('El análisis de calidad ya fue solicitado o se encuentra aprobado.')

        # Validar que ningun reactivo tenga cantidad utilizada negativa. Se
        # permite 0: el material se entrego pero NO se uso (se devuelve todo
        # en la conciliacion, que es obligatoria antes de cerrar).
        sin_cantidad = self.move_raw_ids.filtered(lambda m: (m.quantity or 0.0) < 0)
        if sin_cantidad:
            nombres = ', '.join(sin_cantidad.mapped('product_id.name'))
            raise UserError(f'Los siguientes reactivos tienen Cantidad Utilizada inválida (negativa):\n{nombres}')

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

    # ── Aprobación / rechazo SIMPLE del análisis de PT (Calidad, con PIN) ────
    # Flujo simple mientras se valida: Calidad (Diana) aprueba o rechaza el
    # análisis de producto terminado con su PIN, sin pasar por toda la lógica
    # del módulo de calidad. El enganche al módulo se hará después.
    def action_amunet_qc_aprobar(self):
        self.ensure_one()
        if self.quality_analysis_status != 'requested':
            raise UserError(_('Solo se puede aprobar un análisis que esté en estado "Análisis Solicitado".'))
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_amunet_qc_firma_aprobar',
            _('Aprobación de análisis de PT'),
            _('Firma de Calidad que APRUEBA el análisis del producto terminado de %s.') % self.name)

    def action_amunet_qc_rechazar(self):
        self.ensure_one()
        if self.quality_analysis_status != 'requested':
            raise UserError(_('Solo se puede rechazar un análisis que esté en estado "Análisis Solicitado".'))
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_amunet_qc_firma_rechazar',
            _('Rechazo de análisis de PT'),
            _('Firma de Calidad que RECHAZA el análisis del producto terminado de %s.') % self.name)

    def _amunet_qc_firma_aprobar(self):
        self.ensure_one()
        self.sudo().write({
            'quality_analysis_status': 'approved',
            'amunet_pt_qc_por_id': self.env.user.id,
            'amunet_pt_qc_fecha': fields.Datetime.now(),
        })
        self.sudo().message_post(body=_(
            'Análisis de producto terminado <b>APROBADO</b> por <b>%s</b>.') % self.env.user.name)
        self._amunet_crear_entrega_pt()
        return True

    def _amunet_crear_entrega_pt(self):
        """Al aprobar el analisis del PT, genera la ENTREGA (traslado interno
        Almacen Temporal PT -> APT/Existencias) que Almacen validara cuando
        Produccion entregue fisicamente. Al validarla se libera el lote y
        pasa a Posproduccion. Opcion (a) de Mery 2026-08-14."""
        self.ensure_one()
        categ = (self.product_id.categ_id.complete_name or '')
        if not categ.startswith('Producto terminado'):
            return
        temporal = self._amunet_apt_temporal_location()
        if not temporal:
            return
        ptype = self.env['stock.picking.type'].sudo().search([
            ('code', '=', 'internal'),
            ('warehouse_id.code', '=', 'APT'),
            ('default_location_dest_id.complete_name', 'like', '%Existencias%'),
        ], limit=1)
        if not ptype or not ptype.default_location_dest_id:
            return
        dest = ptype.default_location_dest_id
        lots = self.lot_producing_ids
        if not lots:
            return
        Quant = self.env['stock.quant'].sudo()
        quants = Quant.search([
            ('location_id', '=', temporal.id),
            ('lot_id', 'in', lots.ids),
            ('quantity', '>', 0)])
        if not quants:
            return
        Picking = self.env['stock.picking'].sudo()
        if Picking.search_count([
                ('amunet_entrega_mo_id', '=', self.id),
                ('state', 'not in', ('done', 'cancel'))]):
            return  # ya hay una entrega abierta para esta MO
        picking = Picking.create({
            'picking_type_id': ptype.id,
            'location_id': temporal.id,
            'location_dest_id': dest.id,
            'origin': 'Entrega PT %s' % self.name,
            'amunet_es_entrega_pt': True,
            'amunet_entrega_mo_id': self.id,
        })
        total = sum(quants.mapped('quantity'))
        move = self.env['stock.move'].sudo().create({
            'product_id': self.product_id.id,
            'product_uom_qty': total,
            'product_uom': self.product_id.uom_id.id,
            'location_id': temporal.id,
            'location_dest_id': dest.id,
            'picking_id': picking.id,
        })
        picking.action_confirm()
        ML = self.env['stock.move.line'].sudo()
        for q in quants:
            ML.create({
                'move_id': move.id, 'picking_id': picking.id,
                'product_id': self.product_id.id,
                'product_uom_id': self.product_id.uom_id.id,
                'lot_id': q.lot_id.id, 'quantity': q.quantity,
                'location_id': temporal.id, 'location_dest_id': dest.id,
            })
        self.sudo().message_post(body=_(
            'Generada la <b>entrega de producto terminado</b> (%s): Almacén '
            'Temporal PT → Existencias. Pendiente que Almacén la valide cuando '
            'Producción entregue físicamente; al validarla se libera el lote.'
        ) % picking.name)
        return picking

    def _amunet_qc_firma_rechazar(self):
        self.ensure_one()
        self.sudo().write({
            'quality_analysis_status': 'rejected',
            'amunet_pt_qc_por_id': self.env.user.id,
            'amunet_pt_qc_fecha': fields.Datetime.now(),
        })
        self.sudo().message_post(body=_(
            'Análisis de producto terminado <b>RECHAZADO</b> por <b>%s</b>.') % self.env.user.name)
        return True

    def button_mark_done(self):
        """Bloqueo del flujo nativo de la orden de producción"""
        for record in self:
            # Gate de supervisión: una SOLUCION no se puede producir sin la
            # firma del jefe directo (para Flujo B sin analisis; en Flujo A la
            # supervision ya se exigio antes de solicitar analisis).
            if record.amunet_is_solution_product and record.amunet_supervision_state != 'done':
                raise UserError(_(
                    'Falta la SUPERVISIÓN del jefe directo antes de producir la '
                    'solución. Usa "Enviar a supervisión" y espera la firma del jefe.'))
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

            # 1. Validar cantidades utilizadas en reactivos. Se permite 0
            # (material entregado pero NO usado: se devuelve todo en la
            # conciliacion). Solo se bloquea un valor negativo.
            sin_cantidad = record.move_raw_ids.filtered(lambda m: (m.quantity or 0.0) < 0)
            if sin_cantidad:
                nombres = ', '.join(sin_cantidad.mapped('product_id.name'))
                raise UserError(f'ATENCIÓN: Los siguientes reactivos tienen Cantidad Utilizada inválida (negativa):\n{nombres}')

            # 2. Validar Checklist Operativa — SOLO para SOLUCIONES (preparacion
            # quimica: bitacora/calculos/dilucion/aforar). Los kits, reactivos y
            # medios de cultivo no llevan este checklist aunque tengan los flags
            # amunet_sys_req_* puestos (heredados al dar de alta el producto).
            if record.amunet_is_solution_product:
                missing = []
                if record.amunet_sys_req_history and not record.amunet_check_history_log: missing.append("Registro en Bitácoras")
                if record.amunet_sys_req_calc and not record.amunet_check_calculations: missing.append("Cálculos Realizados")
                if record.amunet_sys_req_dilution and not record.amunet_check_dilution: missing.append("Dilución de Reactivos")
                if record.amunet_sys_req_aforar and not record.amunet_check_aforar: missing.append("Aforar")
                if missing:
                    raise UserError('ATENCIÓN: Faltan las siguientes actividades operativas por marcar en la Pestaña de Actividades:\n- ' + '\n- '.join(missing))
            
            # 2. Validar Calidad (solo si el producto lo requiere y NO es desarrollo)
            if record.amunet_sys_req_qc and not record.amunet_es_desarrollo and record.quality_analysis_status != 'approved':
                raise UserError('ATENCIÓN: Este producto requiere Análisis C.C. No puedes "Marcar como Hecho" hasta que el área de Calidad apruebe el análisis.')
                
        return super(MrpProduction, self).button_mark_done()
