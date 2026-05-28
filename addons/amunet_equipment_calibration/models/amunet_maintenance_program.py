# -*- coding: utf-8 -*-

from datetime import date
from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError


MANAGER_GROUP = 'amunet_equipment_calibration.group_equipment_manager'
TECH_GROUP = 'amunet_equipment_calibration.group_maintenance_technician'

MONTH_SELECTION = [
    ('01', 'Enero'), ('02', 'Febrero'), ('03', 'Marzo'),
    ('04', 'Abril'), ('05', 'Mayo'), ('06', 'Junio'),
    ('07', 'Julio'), ('08', 'Agosto'), ('09', 'Septiembre'),
    ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre'),
]

MONTH_MAP = {
    'ENE': '01', 'FEB': '02', 'MAR': '03', 'ABR': '04',
    'MAY': '05', 'JUN': '06', 'JUL': '07', 'AGO': '08',
    'SEP': '09', 'OCT': '10', 'NOV': '11', 'DIC': '12',
}

ACTIVITY_SELECTION = [
    ('GP', 'Mantenimiento general'),
    ('LP', 'Limpieza preventiva'),
    ('RP', 'Revisión preventiva'),
    ('CP', 'Cambio de piezas'),
    ('FP', 'Verificación funcional'),
]

DEPARTMENT_SELECTION = [
    ('ALMACÉN DE MATERIA PRIMA', 'Almacén de Materia Prima'),
    ('SOLUCIONES', 'Soluciones'),
    ('LECTURA Y PRETRATAMIENTO', 'Lectura y Pretratamiento'),
    ('INYECCIÓN', 'Inyección'),
    ('LAMINADO, SECADO Y CORTE', 'Laminado, Secado y Corte'),
    ('ENCARTUCHADO', 'Encartuchado'),
    ('ACONDICIONADO 1', 'Acondicionado 1'),
    ('ACONDICIONADO 2', 'Acondicionado 2'),
    ('ALMACÉN TEMPORAL DE PRODUCTO TERMINADO', 'Almacén Temporal de PT'),
    ('ESTABILIDAD', 'Estabilidad'),
    ('CONTROL DE CALIDAD', 'Control de Calidad'),
    ('DESARROLLO', 'Desarrollo'),
    ('ALMACÉN DE PRODUCTO TERMINADO', 'Almacén de Producto Terminado'),
    ('PRODUCCIÓN DE DESARROLLO MOLECULAR', 'Producción de Desarrollo Molecular'),
    ('VALIDACIÓN', 'Validación'),
]


class AmunetMaintenanceProgram(models.Model):
    _name = 'amunet.maintenance.program'
    _description = 'Programa Anual de Mantenimiento Preventivo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'year desc, id desc'

    name = fields.Char(required=True, tracking=True)
    year = fields.Integer(
        required=True,
        default=lambda self: date.today().year,
        tracking=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('approved', 'Aprobado'),
        ('active', 'Activo'),
        ('closed', 'Cerrado'),
        ('cancelled', 'Cancelado'),
    ], default='draft', required=True, tracking=True)

    source_document_file = fields.Binary(string='Documento fuente', attachment=True)
    source_document_filename = fields.Char(string='Nombre del documento')
    notes = fields.Text(string='Notas')

    line_ids = fields.One2many(
        'amunet.maintenance.program.line', 'program_id', string='Actividades del programa')

    total_line_count = fields.Integer(compute='_compute_counts', string='Total')
    matched_line_count = fields.Integer(compute='_compute_counts', string='Encontrados')
    missing_line_count = fields.Integer(compute='_compute_counts', string='Faltantes')
    done_line_count = fields.Integer(compute='_compute_counts', string='Realizados')
    pending_line_count = fields.Integer(compute='_compute_counts', string='Pendientes')

    @api.depends('line_ids.match_state', 'line_ids.program_status')
    def _compute_counts(self):
        for program in self:
            lines = program.line_ids
            program.total_line_count = len(lines)
            program.matched_line_count = len(lines.filtered(lambda l: l.match_state == 'matched'))
            program.missing_line_count = len(lines.filtered(lambda l: l.match_state == 'missing'))
            program.done_line_count = len(lines.filtered(lambda l: l.program_status == 'done'))
            program.pending_line_count = len(
                lines.filtered(lambda l: l.program_status == 'p' and l.match_state == 'matched'))

    def action_reconcile(self):
        if not self.env.user.has_group(MANAGER_GROUP):
            raise AccessError('Solo Metrología/Mantenimiento puede reconciliar el programa MVA.')
        for program in self:
            program.line_ids.action_reconcile()
            if program.state == 'draft':
                program.state = 'approved'
            program.message_post(body='Programa reconciliado contra el inventario de equipos.')
        return True

    def action_generate_orders(self):
        if not self.env.user.has_group(MANAGER_GROUP):
            raise AccessError('Solo Metrología/Mantenimiento puede generar órdenes de mantenimiento.')
        created = 0
        for program in self:
            for line in program.line_ids.filtered(
                    lambda l: l.match_state == 'matched'
                    and l.program_status == 'p'
                    and not l.maintenance_id):
                order = self.env['amunet.equipment.maintenance'].create({
                    'equipment_id': line.equipment_id.id,
                    'maintenance_type': line._activity_to_maintenance_type(),
                    'scheduled_date': line.planned_date or date(program.year, int(line.month), 1),
                })
                line.maintenance_id = order
                created += 1
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Órdenes generadas',
                'message': 'Se crearon %d órdenes de mantenimiento.' % created,
                'type': 'success',
                'sticky': False,
            },
        }

    def action_approve(self):
        if not self.env.user.has_group(MANAGER_GROUP):
            raise AccessError('Solo Metrología/Mantenimiento puede aprobar el programa.')
        self.write({'state': 'approved'})

    def action_activate(self):
        if not self.env.user.has_group(MANAGER_GROUP):
            raise AccessError('Solo Metrología/Mantenimiento puede activar el programa.')
        self.write({'state': 'active'})

    def action_close(self):
        if not self.env.user.has_group(MANAGER_GROUP):
            raise AccessError('Solo Metrología/Mantenimiento puede cerrar el programa.')
        self.write({'state': 'closed'})


class AmunetMaintenanceProgramLine(models.Model):
    _name = 'amunet.maintenance.program.line'
    _description = 'Línea del Programa Anual de Mantenimiento'
    _inherit = ['mail.thread']
    _order = 'program_id, department, planned_date, identification_code'

    name = fields.Char(compute='_compute_name', store=True)

    program_id = fields.Many2one(
        'amunet.maintenance.program', required=True, ondelete='cascade', index=True)
    year = fields.Integer(related='program_id.year', store=True)

    mva_equipment_name = fields.Char(string='Nombre en MVA', required=True)
    identification_code = fields.Char(
        string='Código de identificación', required=True, index=True, tracking=True)
    area_name = fields.Char(string='Área (MVA)')

    month = fields.Selection(MONTH_SELECTION, string='Mes', required=True)
    planned_date = fields.Date(
        string='Fecha programada', compute='_compute_planned_date', store=True)
    activity_type = fields.Selection(
        ACTIVITY_SELECTION, string='Actividad', required=True, tracking=True)

    equipment_id = fields.Many2one(
        'amunet.equipment', string='Equipo en Odoo', tracking=True)
    match_state = fields.Selection([
        ('pending', 'Sin revisar'),
        ('matched', 'Encontrado'),
        ('missing', 'Falta en sistema'),
    ], string='Coincidencia', default='pending', required=True, tracking=True)

    area_prefix = fields.Char(
        string='Prefijo área', compute='_compute_code_parts', store=True)
    equipment_family = fields.Char(
        string='Familia', compute='_compute_code_parts', store=True)
    department = fields.Selection(
        DEPARTMENT_SELECTION, string='Área aprobada', tracking=True)

    program_status = fields.Selection([
        ('p', 'Programado'),
        ('done', 'Realizado'),
        ('cancelled', 'Cancelado'),
        ('na', 'No aplica'),
    ], string='Estado', default='p', required=True, tracking=True)

    maintenance_id = fields.Many2one(
        'amunet.equipment.maintenance',
        string='Orden de mantenimiento',
        readonly=True)
    notes = fields.Text(string='Notas')

    @api.depends('identification_code', 'mva_equipment_name', 'month', 'activity_type')
    def _compute_name(self):
        month_labels = dict(MONTH_SELECTION)
        activity_labels = dict(ACTIVITY_SELECTION)
        for line in self:
            line.name = '%s · %s · %s' % (
                line.identification_code or 'Sin código',
                month_labels.get(line.month, line.month or ''),
                activity_labels.get(line.activity_type, line.activity_type or ''),
            )

    @api.depends('program_id.year', 'month')
    def _compute_planned_date(self):
        for line in self:
            if line.program_id.year and line.month:
                line.planned_date = date(line.program_id.year, int(line.month), 1)
            else:
                line.planned_date = False

    @api.depends('identification_code')
    def _compute_code_parts(self):
        for line in self:
            parts = (line.identification_code or '').split('/')
            line.area_prefix = parts[0] if parts else False
            line.equipment_family = parts[1] if len(parts) > 1 else False

    def _suggest_department(self, equipment=False):
        self.ensure_one()
        if equipment and equipment.department:
            return equipment.department
        prefix = (self.area_prefix or '').upper()
        family = (self.equipment_family or '').upper()
        mapping = {
            'CAL': 'CONTROL DE CALIDAD',
            'DES': 'DESARROLLO',
            'EST': 'ESTABILIDAD',
            'ALM': 'ALMACÉN DE MATERIA PRIMA',
            'ALT': 'ALMACÉN TEMPORAL DE PRODUCTO TERMINADO',
            'ALP': 'ALMACÉN DE PRODUCTO TERMINADO',
            'VAL': 'VALIDACIÓN',
        }
        if prefix in mapping:
            return mapping[prefix]
        if prefix == 'PRO':
            if family in ('AGO', 'HOR', 'ESP', 'AMO'):
                return 'LECTURA Y PRETRATAMIENTO'
            if family in ('BOM', 'INY'):
                return 'INYECCIÓN'
            if family in ('COH', 'COT'):
                return 'LAMINADO, SECADO Y CORTE'
            if family in ('SEC',):
                return 'ENCARTUCHADO'
            if family in ('SEL',):
                return 'ACONDICIONADO 1'
            if family in ('IMP',):
                return 'ACONDICIONADO 2'
            return 'SOLUCIONES'
        return False

    def action_reconcile(self):
        if not self.env.user.has_group(MANAGER_GROUP):
            raise AccessError('Solo Metrología/Mantenimiento puede reconciliar.')
        Equipment = self.env['amunet.equipment'].sudo()
        for line in self:
            equipment = Equipment.search(
                [('serial_number', '=', line.identification_code)], limit=1)
            department = line._suggest_department(equipment)
            line.write({
                'equipment_id': equipment.id if equipment else False,
                'match_state': 'matched' if equipment else 'missing',
                'department': line.department or department,
            })
        return True

    def _activity_to_maintenance_type(self):
        self.ensure_one()
        mapping = {
            'LP': 'cleaning',
            'RP': 'preventive',
            'GP': 'preventive',
            'CP': 'preventive',
            'FP': 'preventive',
        }
        return mapping.get(self.activity_type, 'preventive')
