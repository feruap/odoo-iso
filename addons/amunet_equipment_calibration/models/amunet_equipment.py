# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date

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
