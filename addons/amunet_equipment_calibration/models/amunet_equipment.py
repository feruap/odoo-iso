# -*- coding: utf-8 -*-

import calendar
from odoo import models, fields, api
from odoo.exceptions import AccessError, ValidationError
from datetime import date, timedelta

EQUIPMENT_MANAGER_GROUP = 'amunet_equipment_calibration.group_equipment_manager'
MAINTENANCE_TECH_GROUP = 'amunet_equipment_calibration.group_maintenance_technician'

class AmunetEquipment(models.Model):
    _name = 'amunet.equipment'
    _description = 'Equipo de Medición (ISO 13485 Cláusula 7.6)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre del Equipo', required=True, tracking=True)
    serial_number = fields.Char(string='Código/ID', tracking=True)
    brand = fields.Char(string='Marca')
    model_name = fields.Char(string='Modelo')
    department = fields.Selection([
        ('ALMACÉN DE MATERIA PRIMA', 'Almacén de Materia Prima'),
        ('SOLUCIONES', 'Soluciones'),
        ('LECTURA Y PRETRATAMIENTO', 'Lectura y Pretratamiento'),
        ('INYECCIÓN', 'Inyección'),
        ('LAMINADO, SECADO Y CORTE', 'Laminado, Secado y Corte'),
        ('ENCARTUCHADO', 'Encartuchado'),
        ('ACONDICIONADO 1', 'Acondicionado 1'),
        ('ACONDICIONADO 2', 'Acondicionado 2'),
        ('ALMACÉN TEMPORAL DE PRODUCTO TERMINADO', 'Almacén Temporal de Producto Terminado'),
        ('ESTABILIDAD', 'Estabilidad'),
        ('CONTROL DE CALIDAD', 'Control de Calidad'),
        ('DESARROLLO', 'Desarrollo'),
        ('ALMACÉN DE PRODUCTO TERMINADO', 'Almacén de Producto Terminado'),
        ('VALIDACIÓN', 'Validación'),
    ], string='Departamento', tracking=True)
    location_id = fields.Many2one('stock.location', string='Ubicación')

    parent_equipment_id = fields.Many2one(
        'amunet.equipment',
        string='Equipo padre (grupo)',
        ondelete='restrict',
        tracking=True,
        help='Equipo al que pertenece este accesorio o instrumento '
             '(ej. la bomba a la que pertenece un manómetro). '
             'Si está vacío, este es un equipo "crudo" (raíz).'
    )
    child_equipment_ids = fields.One2many(
        'amunet.equipment',
        'parent_equipment_id',
        string='Accesorios / instrumentos'
    )
    child_equipment_count = fields.Integer(
        string='Accesorios',
        compute='_compute_child_equipment_count'
    )
    parent_equipment_group = fields.Char(
        string='Equipo padre',
        compute='_compute_parent_equipment_group',
        store=True,
        help='Texto para agrupación: nombre del padre o "No aplica" si es equipo crudo.'
    )

    is_deseable = fields.Boolean(
        string='Deseable',
        default=False,
        tracking=True,
        help='Marcar si este equipo está físicamente pero no entra al programa de '
             'calibración / mantenimiento. Queda "olvidado por ahora" hasta que '
             'se decida promoverlo o darlo de baja.'
    )
    oficial_status_group = fields.Char(
        string='Clasificación',
        compute='_compute_oficial_status_group',
        store=True,
        help='Etiqueta para agrupación: "Oficial" o "DESEABLES".'
    )

    state = fields.Selection([
        ('active', 'Activo'),
        ('maintenance', 'Pausa'),
        ('out_of_service', 'Inactivo'),
    ], string='Estatus', default='active', tracking=True, required=True)

    calibration_line_ids = fields.One2many(
        'amunet.equipment.calibration',
        'equipment_id',
        string='Historial de Calibración'
    )

    next_calibration_date = fields.Date(
        string='Próxima Calibración',
        compute='_compute_next_calibration',
        store=True,
        tracking=True
    )

    # ========================================================================
    # PUENTE EQUIPO ↔ PNO  (ISO 13485 §6.2 + §7.6)
    # Agregado por Claude — Mayo 2026 (configuración inicial HR/Equipos)
    # ========================================================================
    procedure_ids = fields.Many2many(
        'amunet.quality.procedure',
        'amunet_equipment_procedure_rel',
        'equipment_id',
        'procedure_id',
        string='PNOs Aplicables',
        domain=[('active', '=', True)],
        help='Procedimientos aplicables al equipo (Operación, Limpieza, Mantenimiento). '
             'Un usuario está autorizado para usar este equipo cuando tiene capacitación '
             'vigente en todos los PNOs marcados como de Operación.'
    )

    calibration_required = fields.Boolean(
        string='Requiere Calibración (§7.6)',
        default=True,
        tracking=True,
        help='Desmarcar si el equipo no requiere certificado de calibración formal '
             '(ej. regla, cronómetro, lámpara). Esto evita que el CRON lo ponga '
             'fuera de servicio.'
    )

    qualification_required = fields.Boolean(
        string='Requiere Calificación',
        default=False,
        tracking=True,
        help='El equipo requiere calificación (además de o en vez de calibración). '
             'Lo determina Ensayo/Calibración al ingresar el equipo.'
    )

    calibration_program_line_ids = fields.One2many(
        'amunet.calibration.program.line',
        'equipment_id',
        string='Líneas de programa FVA',
    )
    in_calibration_program = fields.Boolean(
        string='En programa FVA',
        compute='_compute_in_calibration_program',
        store=True,
        help='Verdadero si el equipo tiene al menos una línea activa en el programa FVA.',
    )

    authorized_user_count = fields.Integer(
        string='Usuarios Autorizados',
        compute='_compute_authorized_user_count',
        help='Cantidad de usuarios con capacitación vigente para operar este equipo.'
    )

    calibration_work_status = fields.Selection([
        ('no_required', 'No requiere'),
        ('missing', 'Sin certificado vigente'),
        ('expired', 'Vencida'),
        ('due_soon', 'Por vencer'),
        ('current', 'Vigente'),
    ], string='Estado metrologico', compute='_compute_workqueue_status')
    calibration_next_step = fields.Char(
        string='Siguiente paso metrologia',
        compute='_compute_workqueue_status')

    calibration_queue_status = fields.Selection([
        ('vencido', 'Vencido'),
        ('por_vencer', 'Por vencer'),
        ('sin_certificado', 'Sin certificado'),
        ('cert_cargado', 'Certificado cargado'),
        ('aprobado', 'Vigente'),
    ], string='Estado cola',
       compute='_compute_calibration_queue_status',
       search='_search_calibration_queue_status')

    calibration_responsible_id = fields.Many2one(
        'res.users',
        string='Responsable calibración',
        tracking=True,
    )

    maintenance_required = fields.Boolean(
        string='Requiere mantenimiento',
        default=True,
        tracking=True)
    maintenance_frequency_days = fields.Integer(
        string='Frecuencia mantenimiento (dias)',
        default=180,
        tracking=True)
    maintenance_responsible_id = fields.Many2one(
        'res.users',
        string='Responsable mantenimiento',
        tracking=True)
    maintenance_line_ids = fields.One2many(
        'amunet.equipment.maintenance',
        'equipment_id',
        string='Historial de mantenimiento')
    next_maintenance_date = fields.Date(
        string='Proximo mantenimiento',
        compute='_compute_workqueue_status')
    maintenance_status = fields.Selection([
        ('no_required', 'No requiere'),
        ('missing', 'Sin programa'),
        ('overdue', 'Vencido'),
        ('due_soon', 'Por vencer'),
        ('scheduled', 'Programado'),
        ('in_progress', 'En curso'),
        ('current', 'Vigente'),
    ], string='Estado mantenimiento', compute='_compute_workqueue_status')
    maintenance_next_step = fields.Char(
        string='Siguiente paso mantenimiento',
        compute='_compute_workqueue_status')
    maintenance_open_count = fields.Integer(
        string='Mantenimientos abiertos',
        compute='_compute_workqueue_status')

    expediente_count = fields.Integer(
        string='Cantidad de expedientes',
        compute='_compute_expediente_count',
    )
    expediente_ids = fields.One2many(
        'amunet.equipment.expediente',
        'equipment_id',
        string='Expedientes de Calificación',
    )
    expediente_state = fields.Selection([
        ('en_proceso', 'En proceso'),
        ('vigente', 'Vigente'),
        ('obsoleto', 'Obsoleto'),
    ], string='Estado calificación', compute='_compute_expediente_state')

    has_calibratable_children = fields.Boolean(
        compute='_compute_has_calibratable_children',
        store=True,
    )
    calibracion_via = fields.Char(
        string='Calibración',
        compute='_compute_calibracion_via',
    )

    @api.depends('calibration_program_line_ids.program_status')
    def _compute_in_calibration_program(self):
        for eq in self:
            eq.in_calibration_program = any(
                l.program_status != 'na'
                for l in eq.calibration_program_line_ids
            )

    def _compute_child_equipment_count(self):
        for eq in self:
            eq.child_equipment_count = len(eq.child_equipment_ids)

    def _compute_expediente_count(self):
        Expediente = self.env['amunet.equipment.expediente']
        for eq in self:
            eq.expediente_count = Expediente.search_count([('equipment_id', '=', eq.id)])

    def _compute_expediente_state(self):
        for eq in self:
            exp = (eq.expediente_ids.filtered(lambda e: e.state == 'vigente')[:1]
                   or eq.expediente_ids.filtered(lambda e: e.state == 'en_proceso')[:1]
                   or eq.expediente_ids[:1])
            eq.expediente_state = exp.state if exp else False

    @api.depends('child_equipment_ids.calibration_required')
    def _compute_has_calibratable_children(self):
        for eq in self:
            eq.has_calibratable_children = any(
                c.calibration_required for c in eq.child_equipment_ids
            )

    def _compute_calibracion_via(self):
        for eq in self:
            cal_children = eq.child_equipment_ids.filtered(lambda c: c.calibration_required)
            if cal_children:
                eq.calibracion_via = f'Vía accesorios ({len(cal_children)})'
            elif eq.calibration_required:
                eq.calibracion_via = 'Directa'
            else:
                eq.calibracion_via = '—'

    @api.depends(
        'calibration_required',
        'next_calibration_date',
        'calibration_line_ids.state',
        'calibration_line_ids.certificate_file',
        'calibration_line_ids.expiration_date',
    )
    def _compute_calibration_queue_status(self):
        today = fields.Date.today()
        warning_limit = today + timedelta(days=30)
        grace_deadline = self._calibration_grace_deadline()
        in_grace = bool(grace_deadline and today <= grace_deadline)
        for eq in self:
            if not eq.calibration_required:
                eq.calibration_queue_status = False
                continue
            has_draft_cert = any(
                c.state == 'draft' and c.certificate_file
                for c in eq.calibration_line_ids
            )
            done = eq.calibration_line_ids.filtered(
                lambda c: c.state == 'done' and c.expiration_date
            ).sorted(lambda c: c.expiration_date, reverse=True)
            if done and done[0].expiration_date >= today:
                if done[0].expiration_date <= warning_limit:
                    eq.calibration_queue_status = 'por_vencer'
                else:
                    eq.calibration_queue_status = 'aprobado'
            elif has_draft_cert:
                eq.calibration_queue_status = 'cert_cargado'
            elif in_grace:
                eq.calibration_queue_status = 'por_vencer'
            elif not eq.next_calibration_date:
                eq.calibration_queue_status = 'sin_certificado'
            else:
                eq.calibration_queue_status = 'vencido'

    def _search_calibration_queue_status(self, operator, value):
        today = fields.Date.today()
        warning_limit = today + timedelta(days=30)
        grace_deadline = self._calibration_grace_deadline()
        in_grace = bool(grace_deadline and today <= grace_deadline)

        if operator not in ('=', 'in', '!=', 'not in'):
            return [('id', '=', False)]

        values = [value] if isinstance(value, str) else list(value)
        if operator in ('!=', 'not in'):
            all_states = ['vencido', 'por_vencer', 'sin_certificado', 'cert_cargado', 'aprobado']
            values = [s for s in all_states if s not in values]

        def _draft_cert_ids():
            return self.env['amunet.equipment.calibration'].search([
                ('state', '=', 'draft'),
                ('certificate_file', '!=', False),
            ]).mapped('equipment_id').ids

        domains = []
        for v in values:
            if v == 'aprobado':
                domains.append([
                    ('calibration_required', '=', True),
                    ('next_calibration_date', '>', warning_limit),
                ])
            elif v == 'por_vencer':
                if in_grace:
                    draft_ids = _draft_cert_ids()
                    # calibration_required AND NOT draft_cert AND (no_date OR date <= warning_limit)
                    domains.append([
                        ('calibration_required', '=', True),
                        ('id', 'not in', draft_ids),
                        '|',
                        ('next_calibration_date', '=', False),
                        ('next_calibration_date', '<=', warning_limit),
                    ])
                else:
                    domains.append([
                        ('calibration_required', '=', True),
                        ('next_calibration_date', '>=', today),
                        ('next_calibration_date', '<=', warning_limit),
                    ])
            elif v == 'vencido':
                if in_grace:
                    domains.append([('id', '=', False)])
                else:
                    domains.append([
                        ('calibration_required', '=', True),
                        ('next_calibration_date', '<', today),
                        ('next_calibration_date', '!=', False),
                    ])
            elif v == 'sin_certificado':
                if in_grace:
                    domains.append([('id', '=', False)])
                else:
                    draft_ids = _draft_cert_ids()
                    domains.append([
                        ('calibration_required', '=', True),
                        ('next_calibration_date', '=', False),
                        ('id', 'not in', draft_ids),
                    ])
            elif v == 'cert_cargado':
                draft_ids = _draft_cert_ids()
                domains.append([('id', 'in', draft_ids)])

        if not domains:
            return [('id', '=', False)]
        if len(domains) == 1:
            return domains[0]
        # OR de todos los dominios: ['|', d1..., '|', d2..., d3...]
        result = domains[0]
        for d in domains[1:]:
            result = ['|'] + result + d
        return result

    def action_view_expediente(self):
        self.ensure_one()
        expedientes = self.env['amunet.equipment.expediente'].search(
            [('equipment_id', '=', self.id)])
        if len(expedientes) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Expediente de Calificación',
                'res_model': 'amunet.equipment.expediente',
                'res_id': expedientes.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return {
            'type': 'ir.actions.act_window',
            'name': f'Expedientes de {self.name}',
            'res_model': 'amunet.equipment.expediente',
            'view_mode': 'list,form',
            'domain': [('equipment_id', '=', self.id)],
            'context': {'default_equipment_id': self.id},
            'target': 'current',
        }

    @api.depends('parent_equipment_id', 'parent_equipment_id.name', 'parent_equipment_id.serial_number')
    def _compute_parent_equipment_group(self):
        for eq in self:
            p = eq.parent_equipment_id
            if not p:
                eq.parent_equipment_group = 'No aplica'
            elif p.serial_number:
                eq.parent_equipment_group = f"{p.serial_number} — {p.name}"
            else:
                eq.parent_equipment_group = p.name

    @api.depends('is_deseable')
    def _compute_oficial_status_group(self):
        for eq in self:
            eq.oficial_status_group = 'Deseables' if eq.is_deseable else 'Oficial'

    def _sync_calibration_required_from_lines(self):
        """Ajusta calibration_required en función de las líneas del programa:
        - Si alguna línea tiene program_status='p' (Pendiente) -> True.
        - Si todas las líneas son 'na' (no aplica) -> False.
        - Si no tiene líneas: no cambiar (decisión manual).
        """
        ProgramLine = self.env['amunet.calibration.program.line'].sudo()
        for eq in self:
            lines = ProgramLine.search([('equipment_id', '=', eq.id)])
            if not lines:
                continue
            statuses = set(lines.mapped('program_status'))
            target = False if statuses and statuses.issubset({'na', 'cancelled'}) else True
            if eq.calibration_required != target:
                eq.calibration_required = target

    @api.constrains('parent_equipment_id')
    def _check_parent_equipment(self):
        for eq in self:
            if not eq.parent_equipment_id:
                continue
            if eq.parent_equipment_id.id == eq.id:
                raise ValidationError(
                    f"El equipo '{eq.name}' no puede ser su propio padre."
                )
            if eq.parent_equipment_id.parent_equipment_id:
                raise ValidationError(
                    f"El equipo padre '{eq.parent_equipment_id.name}' ya es un "
                    f"accesorio de otro equipo. Solo se admite un nivel de jerarquía "
                    f"(equipo crudo → accesorio); no se admite anidar accesorios de accesorios."
                )
            if eq.child_equipment_ids:
                raise ValidationError(
                    f"El equipo '{eq.name}' ya tiene accesorios y no puede a su vez "
                    f"colgar de otro equipo padre."
                )

    def action_view_calibration_history(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Calibraciones — {self.name}',
            'res_model': 'amunet.equipment',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_child_equipments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Accesorios de {self.name}',
            'res_model': 'amunet.equipment',
            'view_mode': 'list,form',
            'domain': [('parent_equipment_id', '=', self.id)],
            'context': {'default_parent_equipment_id': self.id,
                        'default_department': self.department,
                        'default_location_id': self.location_id.id},
        }

    @api.depends('calibration_line_ids.state', 'calibration_line_ids.expiration_date')
    def _compute_next_calibration(self):
        ProgramLine = self.env['amunet.calibration.program.line']
        for equipment in self:
            done_cals = equipment.calibration_line_ids.filtered(lambda c: c.state == 'done')
            if done_cals:
                latest = done_cals.sorted(key=lambda c: c.expiration_date, reverse=True)[0]
                equipment.next_calibration_date = latest.expiration_date
            else:
                # Sin certificado: usar último día del mes programado en el FVA
                fva = ProgramLine.search([
                    ('equipment_id', '=', equipment.id),
                    ('program_status', '!=', 'na'),
                    ('planned_month', '!=', False),
                ], order='program_id desc', limit=1)
                if fva and fva.program_id.year:
                    yr = fva.program_id.year
                    mo = int(fva.planned_month)
                    last_day = calendar.monthrange(yr, mo)[1]
                    equipment.next_calibration_date = date(yr, mo, last_day)
                else:
                    equipment.next_calibration_date = False

    def _compute_authorized_user_count(self):
        for eq in self:
            eq.authorized_user_count = len(eq.get_authorized_users())

    @api.depends(
        'calibration_required',
        'next_calibration_date',
        'maintenance_required',
        'maintenance_frequency_days',
        'maintenance_line_ids.state',
        'maintenance_line_ids.scheduled_date',
        'maintenance_line_ids.completed_date',
    )
    def _calibration_grace_deadline(self):
        param = self.env['ir.config_parameter'].sudo().get_param(
            'amunet.calibration.grace.deadline')
        return fields.Date.from_string(param) if param else False

    def _compute_workqueue_status(self):
        today = fields.Date.today()
        warning_limit = today + timedelta(days=30)
        grace_deadline = self._calibration_grace_deadline()
        in_grace = bool(grace_deadline and today <= grace_deadline)
        for eq in self:
            if not eq.calibration_required:
                eq.calibration_work_status = 'no_required'
                eq.calibration_next_step = 'Sin accion metrologica'
            elif not eq.next_calibration_date:
                if in_grace:
                    eq.calibration_work_status = 'due_soon'
                    eq.calibration_next_step = f'Sin certificado — cargar antes del {grace_deadline} para no bloquear'
                else:
                    eq.calibration_work_status = 'missing'
                    eq.calibration_next_step = 'Registrar certificado o reconciliar FVA'
            elif eq.next_calibration_date < today:
                if in_grace:
                    eq.calibration_work_status = 'due_soon'
                    eq.calibration_next_step = f'Calibracion vencida — cargar antes del {grace_deadline} para no bloquear'
                else:
                    eq.calibration_work_status = 'expired'
                    eq.calibration_next_step = 'Bloquear equipo y cargar calibracion vigente'
            elif eq.next_calibration_date <= warning_limit:
                eq.calibration_work_status = 'due_soon'
                eq.calibration_next_step = 'Programar calibracion antes del vencimiento'
            else:
                eq.calibration_work_status = 'current'
                eq.calibration_next_step = 'Sin accion inmediata'

            open_lines = eq.maintenance_line_ids.filtered(
                lambda line: line.state in ('draft', 'scheduled', 'in_progress'))
            eq.maintenance_open_count = len(open_lines)
            if not eq.maintenance_required:
                eq.next_maintenance_date = False
                eq.maintenance_status = 'no_required'
                eq.maintenance_next_step = 'Sin accion de mantenimiento'
                continue

            scheduled = open_lines.sorted(lambda line: line.scheduled_date or date.max)
            done = eq.maintenance_line_ids.filtered(
                lambda line: line.state == 'done' and line.completed_date)
            last_done = done.sorted(lambda line: line.completed_date, reverse=True)[:1]
            if scheduled:
                next_date = scheduled[0].scheduled_date
            elif last_done and eq.maintenance_frequency_days:
                next_date = last_done.completed_date + timedelta(days=eq.maintenance_frequency_days)
            else:
                next_date = False

            eq.next_maintenance_date = next_date
            if open_lines.filtered(lambda line: line.state == 'in_progress'):
                eq.maintenance_status = 'in_progress'
                eq.maintenance_next_step = 'Cerrar mantenimiento y anexar evidencia'
            elif scheduled:
                eq.maintenance_status = 'scheduled'
                eq.maintenance_next_step = 'Ejecutar mantenimiento programado'
            elif not next_date:
                eq.maintenance_status = 'missing'
                eq.maintenance_next_step = 'Programar mantenimiento preventivo'
            elif next_date < today:
                eq.maintenance_status = 'overdue'
                eq.maintenance_next_step = 'Ejecutar mantenimiento vencido'
            elif next_date <= warning_limit:
                eq.maintenance_status = 'due_soon'
                eq.maintenance_next_step = 'Programar mantenimiento proximo'
            else:
                eq.maintenance_status = 'current'
                eq.maintenance_next_step = 'Sin accion inmediata'

    @api.constrains('state', 'next_calibration_date', 'calibration_required')
    def _check_calibration_validity(self):
        """Validación en tiempo real (si alguien intenta activar un equipo vencido)."""
        Expediente = self.env['amunet.equipment.expediente']
        today = date.today()
        grace_deadline = self._calibration_grace_deadline()
        in_grace = bool(grace_deadline and today <= grace_deadline)
        for equipment in self:
            if equipment.state == 'active':
                if not Expediente.search_count([('equipment_id', '=', equipment.id)]):
                    raise ValidationError(
                        f"El equipo '{equipment.name}' no puede activarse porque "
                        f"no tiene un expediente de calificación registrado."
                    )
                if (not in_grace
                        and equipment.calibration_required
                        and equipment.next_calibration_date
                        and equipment.next_calibration_date < today):
                    raise ValidationError(
                        f"El equipo '{equipment.name}' no puede estar 'Activo' "
                        f"porque su calibración venció el {equipment.next_calibration_date}."
                    )

    @api.model
    def _cron_check_calibration_status(self):
        """CRON Job diario para buscar equipos Vencidos y forzarlos a Fuera de Servicio."""
        today = date.today()
        grace_deadline = self._calibration_grace_deadline()
        if grace_deadline and today <= grace_deadline:
            return

        expired_equipments = self.search([
            ('state', '=', 'active'),
            ('calibration_required', '=', True),
            ('next_calibration_date', '!=', False),
            ('next_calibration_date', '<', today)
        ])

        for eq in expired_equipments:
            eq.write({'state': 'out_of_service'})
            eq.message_post(body=(
                f"El sistema ha cambiado automáticamente el estado a 'Fuera de Servicio'. "
                f"Motivo: La calibración caducó el {eq.next_calibration_date}."
            ))

    @api.model
    def _cron_send_calibration_reminders(self):
        """Envía recordatorio el día 1, 15 y último día del mes a los gestores,
        listando equipos calibrables del FVA que aún no tienen certificado vigente."""
        today = date.today()
        last_day = calendar.monthrange(today.year, today.month)[1]
        if today.day not in (1, 15, last_day):
            return

        if today.day == 1:
            aviso = 'INICIO DE MES'
            intro = 'Este mes inicia el periodo de calibración para los siguientes equipos. Coordina el envío al laboratorio o la visita del proveedor:'
        elif today.day == 15:
            aviso = 'MITAD DE MES'
            intro = 'Llevamos 15 días del mes de calibración. Estos equipos aún no tienen certificado registrado en el sistema:'
        else:
            aviso = 'ÚLTIMO AVISO — FIN DE MES'
            intro = 'Hoy es el último día del periodo de calibración. Los siguientes equipos deben tener su certificado cargado antes de mañana o pasarán a estado Inactivo:'

        month_str = str(today.month).zfill(2)
        ProgramLine = self.env['amunet.calibration.program.line']
        fva_lines = ProgramLine.search([
            ('planned_month', '=', month_str),
            ('program_status', '!=', 'na'),
            ('equipment_id', '!=', False),
        ])

        pending = self.env['amunet.equipment']
        for line in fva_lines:
            eq = line.equipment_id
            done = eq.calibration_line_ids.filtered(
                lambda c: c.state == 'done' and c.expiration_date and c.expiration_date >= today
            )
            if not done:
                pending |= eq

        if not pending:
            return

        rows = ''.join(
            f'<tr><td style="padding:4px 8px">{eq.serial_number or ""}</td>'
            f'<td style="padding:4px 8px">{eq.name}</td>'
            f'<td style="padding:4px 8px">{eq.department or ""}</td></tr>'
            for eq in pending.sorted('department')
        )
        body = (
            f'<p>{intro}</p>'
            f'<table border="1" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:13px">'
            f'<tr style="background:#f0f0f0"><th style="padding:4px 8px">Código</th>'
            f'<th style="padding:4px 8px">Equipo</th>'
            f'<th style="padding:4px 8px">Área</th></tr>'
            f'{rows}</table>'
            f'<p>Ver en sistema: '
            f'<a href="https://stagingfc.amunet.com.mx/odoo/equipos-calibracion">Equipos → Calibración</a></p>'
        )

        group = self.env.ref(
            'amunet_equipment_calibration.group_equipment_manager',
            raise_if_not_found=False,
        )
        emails = ','.join(
            u.email for u in (group.users if group else self.env['res.users'])
            if u.email
        )
        if not emails:
            return

        self.env['mail.mail'].sudo().create({
            'subject': f'[Calibración {month_str}/{today.year}] {aviso} — {len(pending)} equipo(s) pendiente(s)',
            'body_html': body,
            'email_to': emails,
            'auto_delete': True,
        }).send()

    # ========================================================================
    # API DE AUTORIZACIÓN
    # ========================================================================
    def get_authorized_users(self):
        """
        Retorna los res.users con capacitación VIGENTE para los PNOs de
        OPERACIÓN del equipo. Si el equipo no tiene PNOs asignados, retorna
        un recordset vacío (= nadie está autorizado explícitamente).

        Un PNO se considera "de Operación" si su code contiene la palabra
        'Operación' o el código empieza con un patrón de operación
        (los PNOs cargados de Amunet tienen 'Operación' en el name).
        """
        self.ensure_one()
        if not self.procedure_ids:
            return self.env['res.users']

        # Filtrar PNOs de operación (heurística por nombre)
        op_procedures = self.procedure_ids.filtered(
            lambda p: 'operac' in (p.name or '').lower()
            or 'operación' in (p.name or '').lower()
        )
        # Si no hay PNOs de "Operación" identificables, tomar todos los PNOs
        # como criterio (más permisivo, mejor para fase inicial).
        if not op_procedures:
            op_procedures = self.procedure_ids

        # Para cada PNO, buscar usuarios con registro vigente
        Registro = self.env['amunet.registro.capacitacion']
        authorized = None
        for proc in op_procedures:
            regs = Registro.search([
                ('procedure_id', '=', proc.id),
                ('state', '=', 'vigente'),
            ])
            users_for_proc = regs.mapped('user_id')
            authorized = users_for_proc if authorized is None else (authorized & users_for_proc)
            if not authorized:
                break
        return authorized or self.env['res.users']

    def action_view_authorized_users(self):
        """Acción de botón para listar los usuarios autorizados."""
        self.ensure_one()
        users = self.get_authorized_users()
        return {
            'name': f'Usuarios autorizados para {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'res.users',
            'view_mode': 'list,form',
            'domain': [('id', 'in', users.ids)],
            'target': 'current',
        }

    def _check_maintenance_access(self):
        if not (
            self.env.user.has_group(EQUIPMENT_MANAGER_GROUP)
            or self.env.user.has_group(MAINTENANCE_TECH_GROUP)
        ):
            raise AccessError('Solo Metrologia/Mantenimiento puede programar mantenimientos.')

    def action_schedule_maintenance(self):
        self._check_maintenance_access()
        Maintenance = self.env['amunet.equipment.maintenance'].sudo()
        for equipment in self:
            open_line = equipment.maintenance_line_ids.filtered(
                lambda line: line.state in ('draft', 'scheduled', 'in_progress'))[:1]
            if open_line:
                maintenance = open_line
            else:
                scheduled_date = equipment.next_maintenance_date or fields.Date.today()
                maintenance = Maintenance.create({
                    'equipment_id': equipment.id,
                    'responsible_id': (
                        equipment.maintenance_responsible_id.id
                        or self.env.user.id
                    ),
                    'scheduled_date': scheduled_date,
                    'state': 'scheduled',
                    'maintenance_type': 'preventive',
                })
                equipment.message_post(
                    body='Mantenimiento programado para %s por %s.'
                    % (scheduled_date, self.env.user.display_name))
            return {
                'type': 'ir.actions.act_window',
                'name': 'Mantenimiento',
                'res_model': 'amunet.equipment.maintenance',
                'res_id': maintenance.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return True

    def action_view_maintenance_lines(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Mantenimientos',
            'res_model': 'amunet.equipment.maintenance',
            'view_mode': 'list,form',
            'domain': [('equipment_id', '=', self.id)],
            'context': {'default_equipment_id': self.id},
            'target': 'current',
        }
