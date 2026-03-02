# -*- coding: utf-8 -*-
import logging
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
