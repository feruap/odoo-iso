# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import _, api, fields, models
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
    procedure_ids = fields.Many2many(
        'amunet.quality.procedure',
        string='PNOs aplicables al equipo',
        related='equipment_id.procedure_ids',
        readonly=True)
    procedure_count = fields.Integer(
        string='PNOs',
        compute='_compute_work_instructions')
    work_instruction = fields.Text(
        string='Que se debe hacer',
        compute='_compute_work_instructions')
    required_evidence = fields.Text(
        string='Evidencia requerida',
        compute='_compute_work_instructions')
    training_status = fields.Selection([
        ('no_pno', 'Sin PNO vinculado'),
        ('no_responsible', 'Sin responsable'),
        ('authorized', 'Responsable autorizado'),
        ('review', 'Revisar capacitacion'),
    ], string='Capacitacion', compute='_compute_work_instructions')
    training_guidance = fields.Char(
        string='Guia de capacitacion',
        compute='_compute_work_instructions')
    checklist_done = fields.Text(
        string='Checklist ejecutado',
        help='Describe los pasos ejecutados, limpieza, inspeccion, ajustes y verificaciones.')
    result = fields.Selection([
        ('pending', 'Pendiente'),
        ('conforme', 'Conforme'),
        ('no_conforme', 'No conforme'),
    ], string='Resultado', default='pending', required=True, tracking=True)
    nonconformity_notes = fields.Text(string='Hallazgo / no conformidad')
    evidence_exception_reason = fields.Char(
        string='Justificacion sin evidencia',
        help='Usar solo si no aplica archivo de evidencia; queda trazado en chatter.')
    performed_by_id = fields.Many2one(
        'res.users', string='Realizo', readonly=True, tracking=True)
    performed_at = fields.Datetime(string='Fecha/hora de cierre', readonly=True, tracking=True)
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

    @api.depends('equipment_id', 'equipment_id.procedure_ids', 'responsible_id', 'maintenance_type')
    def _compute_work_instructions(self):
        type_labels = dict(self._fields['maintenance_type'].selection)
        for record in self:
            procedures = record.procedure_ids
            record.procedure_count = len(procedures)
            type_label = type_labels.get(record.maintenance_type, 'Mantenimiento')

            if not record.equipment_id:
                record.work_instruction = 'Selecciona un equipo para ver el trabajo requerido.'
                record.required_evidence = 'Sin equipo seleccionado.'
                record.training_status = 'no_responsible'
                record.training_guidance = 'Selecciona equipo y responsable.'
                continue

            if procedures:
                pno_names = ', '.join(
                    ('%s %s' % (p.code or '', p.name or '')).strip()
                    for p in procedures
                )
                record.work_instruction = (
                    'Ejecutar mantenimiento %s del equipo %s conforme a los PNOs '
                    'vinculados. Abrir los PNOs antes de iniciar, seguir el checklist '
                    'controlado, registrar cualquier ajuste y cerrar con resultado.'
                ) % (type_label.lower(), record.equipment_id.display_name)
                record.required_evidence = (
                    'Adjuntar evidencia del mantenimiento: checklist firmado, foto, '
                    'reporte interno/externo o registro equivalente. PNOs: %s'
                ) % pno_names
            else:
                record.work_instruction = (
                    'Hallazgo: este equipo no tiene PNO vinculado. No hay instruccion '
                    'controlada visible para el tecnico. Metrologia debe vincular el '
                    'PNO de mantenimiento/limpieza/operacion antes de usarlo como '
                    'evidencia paperless completa.'
                )
                record.required_evidence = (
                    'Adjuntar evidencia del trabajo realizado y documentar que el PNO '
                    'esta pendiente de vinculacion.'
                )

            if not procedures:
                record.training_status = 'no_pno'
                record.training_guidance = 'Vincular PNOs para poder evaluar capacitacion.'
            elif not record.responsible_id:
                record.training_status = 'no_responsible'
                record.training_guidance = 'Asignar responsable.'
            elif record.responsible_id in record.equipment_id.get_authorized_users():
                record.training_status = 'authorized'
                record.training_guidance = 'Responsable con capacitacion vigente para los PNOs vinculados.'
            else:
                record.training_status = 'review'
                record.training_guidance = (
                    'RRHH/Metrologia debe revisar capacitacion vigente del responsable '
                    'contra los PNOs del equipo.'
                )

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

    def action_view_procedures(self):
        self.ensure_one()
        return {
            'name': 'PNOs aplicables a %s' % self.equipment_id.display_name,
            'type': 'ir.actions.act_window',
            'res_model': 'amunet.quality.procedure',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.procedure_ids.ids)],
            'context': {'create': False},
            'target': 'current',
        }

    def _check_close_requirements(self):
        for record in self:
            if not record.checklist_done:
                raise UserError('Antes de cerrar, captura el checklist ejecutado.')
            if record.result == 'pending':
                raise UserError('Antes de cerrar, selecciona Resultado: Conforme o No conforme.')
            if not record.evidence_file and not record.evidence_exception_reason:
                raise UserError(
                    'Antes de cerrar, adjunta evidencia o explica por que no aplica archivo.')
            if record.result == 'no_conforme' and not record.nonconformity_notes:
                raise UserError('Para resultado No conforme, captura el hallazgo/no conformidad.')

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_action_done': _('Cerrar mantenimiento de equipo'),
        }

    def _amunet_signature_required_procedures(self):
        self.ensure_one()
        return self.procedure_ids.filtered('active')

    def action_done(self):
        self.ensure_one()
        self._check_write_access()
        if self.state not in ('draft', 'scheduled', 'in_progress'):
            raise UserError('Solo se puede cerrar un mantenimiento abierto.')
        self._check_close_requirements()
        return self.env['amunet.generic.signature.wizard'].open_for(
            self,
            '_signature_action_done',
            _('Cerrar mantenimiento de equipo'),
            _('Firma de cierre de mantenimiento para %s.') % self.display_name,
        )

    def _signature_action_done(self):
        self.ensure_one()
        self._check_write_access()
        for record in self:
            if record.state not in ('draft', 'scheduled', 'in_progress'):
                raise UserError('Solo se puede cerrar un mantenimiento abierto.')
            record._check_close_requirements()
            record.with_context(amunet_maintenance_signature_write=True).write({
                'state': 'done',
                'completed_date': fields.Date.today(),
                'performed_by_id': self.env.user.id,
                'performed_at': fields.Datetime.now(),
            })
            if record.result == 'no_conforme':
                record.equipment_id.sudo().write({'state': 'out_of_service'})
                record.equipment_id.sudo().message_post(
                    body='Mantenimiento cerrado NO CONFORME por %s. Hallazgo: %s'
                    % (self.env.user.display_name, record.nonconformity_notes))
            elif record.equipment_id.state == 'maintenance':
                record.equipment_id.sudo().write({'state': 'active'})
                record.equipment_id.sudo().message_post(
                    body='Mantenimiento cerrado conforme por %s.' % self.env.user.display_name)
        return True

    def _has_close_signature_values(self, vals):
        return (
            vals.get('state') == 'done'
            or {'completed_date', 'performed_by_id', 'performed_at'}.intersection(vals)
        )

    @api.model_create_multi
    def create(self, vals_list):
        if (
            not self.env.context.get('amunet_maintenance_signature_write')
            and not self.env.su
        ):
            for vals in vals_list:
                if self._has_close_signature_values(vals):
                    raise UserError(_(
                        'El cierre de mantenimiento solo puede registrarse '
                        'desde el wizard de firma electronica.'))
        return super().create(vals_list)

    def write(self, vals):
        if (
            self._has_close_signature_values(vals)
            and not self.env.context.get('amunet_maintenance_signature_write')
            and not self.env.su
        ):
            raise UserError(_(
                'El cierre de mantenimiento solo puede registrarse desde '
                'el wizard de firma electronica.'))
        return super().write(vals)

    def action_cancel(self):
        self._check_write_access()
        self.write({'state': 'cancelled'})
        return True
