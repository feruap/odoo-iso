# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AmunetRegistroCapacitacion(models.Model):
    """
    Registro individual de capacitación de un analista.
    ISO 13485:2016 Cláusula 6.2 - Competencia del personal.

    Garantiza la trazabilidad entre persona, procedimiento y vigencia.
    """
    _name = 'amunet.registro.capacitacion'
    _description = 'Registro de Capacitación (ISO 13485 §6.2)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'expiry_date asc, user_id asc'

    # =========================================================================
    # IDENTIFICACIÓN
    # =========================================================================

    name = fields.Char(
        string='Referencia',
        readonly=True,
        copy=False,
        default='Nuevo',
        help='Número de serie (CAP-XXXX)'
    )

    # Origen: si el registro se generó automáticamente al aprobar un curso.
    intento_id = fields.Many2one(
        'amunet.curso.intento',
        string='Intento de Examen (origen)',
        readonly=True,
        copy=False,
        ondelete='set null',
        help='Intento de examen de curso que generó automáticamente este '
             'registro, si aplica. Vacío = registro capturado manualmente.'
    )

    # =========================================================================
    # QUIÉN
    # =========================================================================

    user_id = fields.Many2one(
        'res.users',
        string='Analista / Usuario',
        required=True,
        index=True,
        tracking=True,
        help='Usuario de Odoo que recibió la capacitación'
    )

    employee_id = fields.Many2one(
        'hr.employee',
        string='Empleado',
        compute='_compute_employee_id',
        store=True,
        help='Empleado vinculado al usuario (calculado automáticamente)'
    )

    department_id = fields.Many2one(
        'hr.department',
        string='Departamento',
        related='employee_id.department_id',
        store=True,
        readonly=True
    )

    # =========================================================================
    # EN QUÉ (Alcance — al menos uno requerido)
    # =========================================================================

    procedure_id = fields.Many2one(
        'amunet.quality.procedure',
        string='SOP / Procedimiento',
        index=True,
        tracking=True,
        domain=[('active', '=', True)],
        help='Procedimiento Operativo Estándar al que aplica esta capacitación'
    )

    parameter_id = fields.Many2one(
        'amunet.quality.check.parameter',
        string='Parámetro de Prueba',
        index=True,
        tracking=True,
        help='Parámetro específico de análisis (opcional, complementa el SOP)'
    )

    # =========================================================================
    # CUÁNDO
    # =========================================================================

    training_date = fields.Date(
        string='Fecha de Capacitación',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )

    expiry_date = fields.Date(
        string='Fecha de Caducidad',
        required=True,
        tracking=True,
        help='Fecha límite de vigencia. Después de esta fecha el analista queda BLOQUEADO para firmar.'
    )

    days_to_expiry = fields.Integer(
        string='Días restantes',
        compute='_compute_days_to_expiry',
        help='Días que quedan hasta la caducidad (negativo = ya venció)'
    )

    # =========================================================================
    # ESTADO
    # =========================================================================

    state = fields.Selection([
        ('vigente', '✅ Vigente'),
        ('proxima', '⚠️ Por vencer (< 30 días)'),
        ('vencida', '❌ Vencida'),
        ('cancelada', '🚫 Cancelada'),
    ], string='Estado', compute='_compute_state', store=True, tracking=True)

    # =========================================================================
    # INSTRUCTOR Y EVIDENCIA
    # =========================================================================

    trainer_id = fields.Many2one(
        'res.users',
        string='Instructor / Capacitador',
        tracking=True
    )

    training_type = fields.Selection([
        ('presencial', 'Presencial'),
        ('virtual', 'Virtual / Webinar'),
        ('autodidacta', 'Autodidacta (lectura SOP)'),
        ('externo', 'Externo (proveedor/consultor)'),
    ], string='Modalidad', default='presencial')

    notes = fields.Text(string='Observaciones')

    certificate_file = fields.Binary(
        string='Constancia / Evidencia',
        attachment=True,
        help='Archivo PDF, imagen o cualquier evidencia documental'
    )
    certificate_filename = fields.Char(string='Nombre archivo')

    # =========================================================================
    # MÉTODOS COMPUTADOS
    # =========================================================================

    @api.depends('user_id')
    def _compute_employee_id(self):
        for rec in self:
            employee = self.env['hr.employee'].search(
                [('user_id', '=', rec.user_id.id)], limit=1
            )
            rec.employee_id = employee

    @api.depends('expiry_date')
    def _compute_days_to_expiry(self):
        today = fields.Date.today()
        for rec in self:
            if rec.expiry_date:
                rec.days_to_expiry = (rec.expiry_date - today).days
            else:
                rec.days_to_expiry = 0

    @api.depends('expiry_date', 'state')
    def _compute_state(self):
        today = fields.Date.today()
        for rec in self:
            if rec.state == 'cancelada':
                continue
            if not rec.expiry_date:
                rec.state = 'vigente'
                continue
            days = (rec.expiry_date - today).days
            if days < 0:
                rec.state = 'vencida'
            elif days <= 30:
                rec.state = 'proxima'
            else:
                rec.state = 'vigente'

    # =========================================================================
    # VALIDACIONES
    # =========================================================================

    @api.constrains('procedure_id', 'parameter_id')
    def _check_scope(self):
        for rec in self:
            if not rec.procedure_id and not rec.parameter_id:
                raise ValidationError(
                    "Debe asociar al menos un SOP/Procedimiento o un Parámetro "
                    "para registrar la capacitación."
                )

    @api.constrains('training_date', 'expiry_date')
    def _check_dates(self):
        for rec in self:
            if rec.expiry_date and rec.training_date and rec.expiry_date <= rec.training_date:
                raise ValidationError(
                    "La fecha de caducidad debe ser posterior a la fecha de capacitación."
                )

    # =========================================================================
    # CRUD
    # =========================================================================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('amunet.registro.capacitacion')
                    or 'CAP-000'
                )
        return super().create(vals_list)

    # =========================================================================
    # ACCIONES
    # =========================================================================

    def action_cancelar(self):
        self.write({'state': 'cancelada'})

    def action_reactivar(self):
        """Reactivar solo si la fecha de caducidad aún es válida."""
        today = fields.Date.today()
        for rec in self:
            if rec.expiry_date and rec.expiry_date >= today:
                rec.state = 'vigente'
            else:
                raise ValidationError(
                    f"No se puede reactivar '{rec.name}': la fecha de caducidad ya pasó. "
                    "Actualice la fecha de caducidad primero."
                )

    def _get_responsable_renovacion(self):
        """Usuario responsable para actividades de renovación de capacitación."""
        self.ensure_one()
        if self.trainer_id and self.trainer_id.active:
            return self.trainer_id
        if self.env.user.has_group('amunet_competencias.group_competencias_manager'):
            return self.env.user
        grupo = self.env.ref(
            'amunet_competencias.group_competencias_manager',
            raise_if_not_found=False)
        if grupo:
            gestor = grupo.sudo().users.filtered('active')[:1]
            if gestor:
                return gestor
        return self.env.user

    def action_programar_renovacion(self):
        """Crea o actualiza actividades para renovar capacitaciones."""
        if not self.env.user.has_group(
                'amunet_competencias.group_competencias_manager'):
            raise ValidationError(
                "Solo el Gestor de Capacitación puede programar renovaciones.")
        activity_type = self.env.ref(
            'mail.mail_activity_data_todo', raise_if_not_found=False)
        if not activity_type:
            raise ValidationError(
                "No se encontró el tipo de actividad 'Por hacer'.")
        today = fields.Date.today()
        for rec in self:
            responsable = rec._get_responsable_renovacion()
            deadline = rec.expiry_date - timedelta(days=7) if rec.expiry_date else today
            if deadline < today:
                deadline = today
            scope = rec.procedure_id.display_name or rec.parameter_id.display_name or 'sin alcance'
            summary = 'Renovar capacitación'
            note = (
                'Renovar capacitación de %s para %s. Vence: %s.'
                % (rec.user_id.display_name, scope, rec.expiry_date or 'sin fecha'))
            existing = rec.activity_ids.filtered(
                lambda a: a.activity_type_id == activity_type
                and a.summary == summary)
            if existing:
                existing.write({
                    'date_deadline': deadline,
                    'user_id': responsable.id,
                    'note': note,
                })
            else:
                rec.activity_schedule(
                    activity_type_id=activity_type.id,
                    summary=summary,
                    note=note,
                    user_id=responsable.id,
                    date_deadline=deadline,
                )
        return True
