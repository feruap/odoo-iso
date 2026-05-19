# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError


EQUIPMENT_MANAGER_GROUP = 'amunet_equipment_calibration.group_equipment_manager'
MAINTENANCE_TECH_GROUP = 'amunet_equipment_calibration.group_maintenance_technician'


class AmunetEquipmentMaintenance(models.Model):
    _name = 'amunet.equipment.maintenance'
    _description = 'Mantenimiento de Equipo Amunet'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_date asc, id desc'

    name = fields.Char(compute='_compute_name', store=True)
    equipment_id = fields.Many2one(
        'amunet.equipment',
        string='Equipo',
        required=True,
        ondelete='cascade',
        tracking=True)
    responsible_id = fields.Many2one(
        'res.users',
        string='Responsable',
        default=lambda self: self.env.user,
        tracking=True)
    maintenance_type = fields.Selection([
        ('preventive', 'Preventivo'),
        ('corrective', 'Correctivo'),
        ('cleaning', 'Limpieza'),
        ('service', 'Servicio externo'),
    ], string='Tipo', default='preventive', required=True, tracking=True)
    scheduled_date = fields.Date(
        string='Fecha programada',
        default=fields.Date.context_today,
        required=True,
        tracking=True)
    started_date = fields.Datetime(string='Inicio real', readonly=True, tracking=True)
    completed_date = fields.Date(string='Fecha de cierre', readonly=True, tracking=True)
    duration_hours = fields.Float(string='Duracion (h)')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('scheduled', 'Programado'),
        ('in_progress', 'En curso'),
        ('done', 'Realizado'),
        ('cancelled', 'Cancelado'),
    ], string='Estado', default='draft', required=True, tracking=True)
    due_status = fields.Selection([
        ('overdue', 'Vencido'),
        ('due_today', 'Hoy'),
        ('due_soon', 'Proximo'),
        ('scheduled', 'Programado'),
        ('done', 'Realizado'),
        ('cancelled', 'Cancelado'),
    ], string='Prioridad', compute='_compute_due_status')
    next_step = fields.Char(string='Siguiente paso', compute='_compute_due_status')
    notes = fields.Text(string='Trabajo realizado / notas')
    evidence_file = fields.Binary(string='Evidencia', attachment=True)
    evidence_filename = fields.Char(string='Nombre archivo')

    @api.depends('equipment_id', 'scheduled_date', 'maintenance_type')
    def _compute_name(self):
        for record in self:
            equipment = record.equipment_id.display_name or 'Equipo'
            scheduled = record.scheduled_date or 'sin fecha'
            record.name = '%s - %s - %s' % (
                equipment,
                dict(record._fields['maintenance_type'].selection).get(
                    record.maintenance_type, 'Mantenimiento'),
                scheduled,
            )

    @api.depends('state', 'scheduled_date')
    def _compute_due_status(self):
        today = fields.Date.today()
        soon = today + timedelta(days=30)
        for record in self:
            if record.state == 'done':
                record.due_status = 'done'
                record.next_step = 'Sin accion'
            elif record.state == 'cancelled':
                record.due_status = 'cancelled'
                record.next_step = 'Sin accion'
            elif record.state == 'in_progress':
                record.due_status = 'due_today'
                record.next_step = 'Cerrar mantenimiento y anexar evidencia'
            elif record.scheduled_date and record.scheduled_date < today:
                record.due_status = 'overdue'
                record.next_step = 'Ejecutar mantenimiento vencido'
            elif record.scheduled_date == today:
                record.due_status = 'due_today'
                record.next_step = 'Ejecutar hoy'
            elif record.scheduled_date and record.scheduled_date <= soon:
                record.due_status = 'due_soon'
                record.next_step = 'Preparar ejecucion'
            else:
                record.due_status = 'scheduled'
                record.next_step = 'Esperar fecha programada'

    def _check_write_access(self):
        if not (
            self.env.user.has_group(EQUIPMENT_MANAGER_GROUP)
            or self.env.user.has_group(MAINTENANCE_TECH_GROUP)
        ):
            raise AccessError('Solo Metrologia/Mantenimiento puede modificar mantenimientos.')

    def action_schedule(self):
        self._check_write_access()
        self.write({'state': 'scheduled'})
        return True

    def action_start(self):
        self._check_write_access()
        for record in self:
            if record.state not in ('draft', 'scheduled'):
                raise UserError('Solo se puede iniciar un mantenimiento en borrador o programado.')
            record.write({
                'state': 'in_progress',
                'started_date': fields.Datetime.now(),
            })
            record.equipment_id.sudo().write({'state': 'maintenance'})
            record.equipment_id.sudo().message_post(
                body='Mantenimiento iniciado por %s.' % self.env.user.display_name)
        return True

    def action_done(self):
        self._check_write_access()
        for record in self:
            if record.state not in ('draft', 'scheduled', 'in_progress'):
                raise UserError('Solo se puede cerrar un mantenimiento abierto.')
            record.write({
                'state': 'done',
                'completed_date': fields.Date.today(),
            })
            if record.equipment_id.state == 'maintenance':
                record.equipment_id.sudo().write({'state': 'active'})
            record.equipment_id.sudo().message_post(
                body='Mantenimiento cerrado por %s.' % self.env.user.display_name)
        return True

    def action_cancel(self):
        self._check_write_access()
        self.write({'state': 'cancelled'})
        return True
