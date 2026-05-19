# -*- coding: utf-8 -*-

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
    serial_number = fields.Char(string='Número de Serie / Fabricante', tracking=True)
    brand = fields.Char(string='Marca')
    model_name = fields.Char(string='Modelo')
    department = fields.Selection([
        ('ALMACÉN DE MATERIA PRIMA', 'Almacén de Materia Prima'),
        ('SOLUCIONES', 'Soluciones'),
        ('LECTURA Y SECADO', 'Lectura y Secado'),
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
        ('PRODUCCIÓN DE DESARROLLO MOLECULAR', 'Producción de Desarrollo Molecular'),
    ], string='Departamento', tracking=True)
    location_id = fields.Many2one('stock.location', string='Ubicación')

    state = fields.Selection([
        ('active', 'Activo'),
        ('maintenance', 'En Mantenimiento / Calibración'),
        ('out_of_service', 'Fuera de Servicio')
    ], string='Estado', default='active', tracking=True, required=True)

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

    @api.depends('calibration_line_ids.state', 'calibration_line_ids.expiration_date')
    def _compute_next_calibration(self):
        for equipment in self:
            active_calibrations = equipment.calibration_line_ids.filtered(lambda c: c.state == 'done')
            if active_calibrations:
                latest_calibration = active_calibrations.sorted(key=lambda c: c.expiration_date, reverse=True)[0]
                equipment.next_calibration_date = latest_calibration.expiration_date
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
    def _compute_workqueue_status(self):
        today = fields.Date.today()
        warning_limit = today + timedelta(days=30)
        for eq in self:
            if not eq.calibration_required:
                eq.calibration_work_status = 'no_required'
                eq.calibration_next_step = 'Sin accion metrologica'
            elif not eq.next_calibration_date:
                eq.calibration_work_status = 'missing'
                eq.calibration_next_step = 'Registrar certificado o reconciliar FVA'
            elif eq.next_calibration_date < today:
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
        for equipment in self:
            if (equipment.state == 'active'
                    and equipment.calibration_required
                    and equipment.next_calibration_date
                    and equipment.next_calibration_date < date.today()):
                raise ValidationError(
                    f"El equipo '{equipment.name}' no puede estar 'Activo' "
                    f"porque su calibración venció el {equipment.next_calibration_date}."
                )

    @api.model
    def _cron_check_calibration_status(self):
        """CRON Job diario para buscar equipos Vencidos y forzarlos a Fuera de Servicio."""
        today = date.today()
        expired_equipments = self.search([
            ('state', '=', 'active'),
            ('calibration_required', '=', True),
            ('next_calibration_date', '!=', False),
            ('next_calibration_date', '<', today)
        ])

        for eq in expired_equipments:
            eq.write({'state': 'out_of_service'})
            eq.message_post(body=(
                f"🔴 El sistema ha cambiado automáticamente el estado a 'Fuera de Servicio'. "
                f"Motivo: La calibración caducó el {eq.next_calibration_date}."
            ))

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
