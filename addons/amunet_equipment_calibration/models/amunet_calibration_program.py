# -*- coding: utf-8 -*-

import re
from datetime import date
from odoo import models, fields, api
from odoo.exceptions import AccessError, UserError


MANAGER_GROUP = 'amunet_equipment_calibration.group_equipment_manager'


def _check_equipment_manager(env):
    if not env.user.has_group(MANAGER_GROUP):
        raise AccessError(
            "Solo el grupo Gestor de Equipos / Metrologia puede modificar el programa FVA."
        )


DEPARTMENT_SELECTION = [
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
]

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


class AmunetCalibrationProgram(models.Model):
    _name = 'amunet.calibration.program'
    _description = 'Programa Anual de Calibracion/Caracterizacion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'year desc, id desc'

    name = fields.Char(required=True, tracking=True)
    year = fields.Integer(required=True, default=lambda self: date.today().year, tracking=True)
    source_document_file = fields.Binary(string='Documento fuente', attachment=True)
    source_document_filename = fields.Char(string='Nombre del documento')
    notes = fields.Text(string='Notas')

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('review', 'En revision'),
        ('approved', 'Aprobado'),
        ('applied', 'Aplicado'),
        ('cancelled', 'Cancelado'),
    ], default='draft', required=True, tracking=True)

    line_ids = fields.One2many(
        'amunet.calibration.program.line', 'program_id', string='Equipos del programa')
    total_line_count = fields.Integer(compute='_compute_counts')
    matched_line_count = fields.Integer(compute='_compute_counts')
    missing_line_count = fields.Integer(compute='_compute_counts')
    mismatch_line_count = fields.Integer(compute='_compute_counts')
    pending_review_count = fields.Integer(compute='_compute_counts')
    approved_line_count = fields.Integer(compute='_compute_counts')
    applied_line_count = fields.Integer(compute='_compute_counts')
    na_line_count = fields.Integer(compute='_compute_counts')

    @api.depends('line_ids.match_state', 'line_ids.review_state', 'line_ids.program_status')
    def _compute_counts(self):
        for program in self:
            lines = program.line_ids
            program.total_line_count = len(lines)
            program.matched_line_count = len(lines.filtered(lambda l: l.match_state == 'matched'))
            program.missing_line_count = len(lines.filtered(lambda l: l.match_state == 'missing'))
            program.mismatch_line_count = len(lines.filtered(lambda l: l.match_state == 'mismatch'))
            program.pending_review_count = len(lines.filtered(lambda l: l.review_state == 'pending'))
            program.approved_line_count = len(lines.filtered(lambda l: l.review_state == 'approved'))
            program.applied_line_count = len(lines.filtered(lambda l: l.review_state == 'applied'))
            program.na_line_count = len(lines.filtered(lambda l: l.program_status == 'na'))

    def action_reconcile(self):
        _check_equipment_manager(self.env)
        for program in self:
            program.line_ids.action_reconcile()
            program.state = 'review'
            program.message_post(body='Programa reconciliado contra el inventario de equipos.')
        return True

    def action_approve_ready_lines(self):
        _check_equipment_manager(self.env)
        for program in self:
            ready = program.line_ids.filtered(
                lambda l: l.review_state in ('pending', 'reviewed')
                and l.match_state == 'matched'
                and l.department_final
                and l.program_status != 'na')
            ready.action_approve_line()
            program.state = 'approved'
        return True

    def action_apply_approved_lines(self):
        _check_equipment_manager(self.env)
        for program in self:
            approved = program.line_ids.filtered(lambda l: l.review_state == 'approved')
            approved.action_apply_to_equipment()
            if not program.line_ids.filtered(lambda l: l.review_state in ('pending', 'reviewed', 'approved')):
                program.state = 'applied'
        return True


class AmunetCalibrationProgramLine(models.Model):
    _name = 'amunet.calibration.program.line'
    _description = 'Linea de Programa Anual de Calibracion/Caracterizacion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'program_id, sequence, identification_code'

    name = fields.Char(compute='_compute_name', store=True)
    sequence = fields.Integer(default=10)
    program_id = fields.Many2one(
        'amunet.calibration.program', required=True, ondelete='cascade', index=True)
    year = fields.Integer(related='program_id.year', store=True)

    fva_equipment_name = fields.Char(string='Nombre en FVA', required=True, tracking=True)
    brand_model_raw = fields.Char(string='Marca/modelo en FVA', tracking=True)
    identification_code = fields.Char(string='Codigo de identificacion', required=True, index=True, tracking=True)
    service_type = fields.Selection([
        ('calibracion', 'Calibracion'),
        ('caracterizacion', 'Caracterizacion'),
    ], string='Tipo de servicio', required=True, default='calibracion', tracking=True)
    planned_month = fields.Selection(MONTH_SELECTION, string='Mes programado', tracking=True)
    planned_date = fields.Date(string='Fecha programada', compute='_compute_planned_date', store=True)
    program_status = fields.Selection([
        ('p', 'Programada'),
        ('r', 'Reprogramada'),
        ('done', 'Realizada'),
        ('cancelled', 'Cancelada'),
        ('na', 'No aplica'),
    ], default='p', required=True, tracking=True)

    equipment_id = fields.Many2one('amunet.equipment', string='Equipo en Odoo', tracking=True)
    match_state = fields.Selection([
        ('pending', 'Sin revisar'),
        ('matched', 'Encontrado'),
        ('missing', 'Falta crear'),
        ('mismatch', 'Diferencias'),
    ], default='pending', required=True, tracking=True)
    review_state = fields.Selection([
        ('pending', 'Pendiente de revisar'),
        ('reviewed', 'Revisado'),
        ('approved', 'Aprobado'),
        ('applied', 'Aplicado a equipo'),
        ('no_apply', 'No aplica'),
    ], default='pending', required=True, tracking=True)

    area_prefix = fields.Char(string='Prefijo de area', compute='_compute_code_parts', store=True)
    equipment_family = fields.Char(string='Familia de equipo', compute='_compute_code_parts', store=True)
    department_suggested = fields.Selection(DEPARTMENT_SELECTION, string='Area sugerida')
    department_final = fields.Selection(DEPARTMENT_SELECTION, string='Area aprobada')
    department_review_note = fields.Char(string='Nota de area')
    requires_calibration = fields.Boolean(string='Requiere control metrologico', default=True)

    pno_candidate_ids = fields.Many2many(
        'amunet.quality.procedure',
        'amunet_cal_program_line_pno_candidate_rel',
        'line_id', 'procedure_id',
        string='PNOs candidatos',
        domain=[('active', '=', True)])
    pno_approved_ids = fields.Many2many(
        'amunet.quality.procedure',
        'amunet_cal_program_line_pno_approved_rel',
        'line_id', 'procedure_id',
        string='PNOs aprobados',
        domain=[('active', '=', True)])

    parsed_brand = fields.Char(string='Marca sugerida')
    parsed_model = fields.Char(string='Modelo sugerido')
    mismatch_notes = fields.Text(string='Diferencias / hallazgos')
    notes = fields.Text(string='Notas de revision')
    workqueue_priority = fields.Selection([
        ('blocked', 'Bloqueante'),
        ('review', 'Revisar'),
        ('ready', 'Lista'),
        ('done', 'Terminado'),
    ], string='Prioridad', compute='_compute_workqueue_guidance')
    workqueue_next_step = fields.Char(
        string='Siguiente paso',
        compute='_compute_workqueue_guidance')
    workqueue_blocker = fields.Char(
        string='Bloqueo / hallazgo',
        compute='_compute_workqueue_guidance')

    @api.depends('identification_code', 'fva_equipment_name')
    def _compute_name(self):
        for line in self:
            line.name = '%s - %s' % (
                line.identification_code or 'Sin codigo',
                line.fva_equipment_name or 'Equipo')

    @api.depends(
        'program_status',
        'match_state',
        'review_state',
        'department_final',
        'equipment_id',
        'pno_approved_ids',
        'mismatch_notes',
    )
    def _compute_workqueue_guidance(self):
        for line in self:
            if line.program_status == 'na':
                line.workqueue_priority = 'done'
                line.workqueue_next_step = 'Sin accion: no aplica en FVA'
                line.workqueue_blocker = False
            elif line.review_state == 'applied':
                line.workqueue_priority = 'done'
                line.workqueue_next_step = 'Aplicado al equipo'
                line.workqueue_blocker = False
            elif line.match_state == 'missing':
                line.workqueue_priority = 'blocked'
                line.workqueue_next_step = 'Crear o vincular equipo en Odoo'
                line.workqueue_blocker = 'Equipo FVA no encontrado en Odoo'
            elif line.match_state == 'mismatch':
                line.workqueue_priority = 'review'
                line.workqueue_next_step = 'Resolver diferencia FVA vs Odoo'
                line.workqueue_blocker = line.mismatch_notes or 'Diferencia pendiente'
            elif not line.department_final:
                line.workqueue_priority = 'review'
                line.workqueue_next_step = 'Confirmar area aprobada'
                line.workqueue_blocker = 'Area sin aprobar'
            elif not line.pno_approved_ids:
                line.workqueue_priority = 'review'
                line.workqueue_next_step = 'Aprobar PNOs aplicables'
                line.workqueue_blocker = 'PNOs sin aprobar'
            elif line.review_state == 'approved':
                line.workqueue_priority = 'ready'
                line.workqueue_next_step = 'Aplicar a equipo'
                line.workqueue_blocker = False
            else:
                line.workqueue_priority = 'ready'
                line.workqueue_next_step = 'Aprobar linea FVA'
                line.workqueue_blocker = False

    @api.depends('identification_code')
    def _compute_code_parts(self):
        for line in self:
            parts = (line.identification_code or '').split('/')
            line.area_prefix = parts[0] if parts else False
            line.equipment_family = parts[1] if len(parts) > 1 else False

    @api.depends('program_id.year', 'planned_month')
    def _compute_planned_date(self):
        for line in self:
            if line.program_id.year and line.planned_month:
                line.planned_date = date(line.program_id.year, int(line.planned_month), 1)
            else:
                line.planned_date = False

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._normalize_from_fva()
        return records

    def write(self, vals):
        res = super().write(vals)
        if {'brand_model_raw', 'identification_code', 'fva_equipment_name', 'program_status'} & set(vals):
            self._normalize_from_fva()
        return res

    def _normalize_from_fva(self):
        for line in self:
            brand, model = line._split_brand_model(line.brand_model_raw)
            updates = {}
            if line.parsed_brand != brand:
                updates['parsed_brand'] = brand
            if line.parsed_model != model:
                updates['parsed_model'] = model
            if line.program_status == 'na' and line.requires_calibration:
                updates['requires_calibration'] = False
            if updates:
                super(AmunetCalibrationProgramLine, line).write(updates)

    @staticmethod
    def _split_brand_model(raw):
        raw = (raw or '').strip()
        if not raw:
            return False, False
        if '/' in raw:
            brand, model = raw.split('/', 1)
            return brand.strip() or False, model.strip() or False
        return False, raw

    def _suggest_department(self, equipment=False):
        self.ensure_one()
        if equipment and equipment.department:
            return equipment.department, False
        prefix = (self.area_prefix or '').upper()
        family = (self.equipment_family or '').upper()
        if prefix == 'CAL':
            return 'CONTROL DE CALIDAD', False
        if prefix == 'DES':
            return 'DESARROLLO', False
        if prefix == 'EST':
            return 'ESTABILIDAD', False
        if prefix == 'ALM':
            return 'ALMACÉN DE MATERIA PRIMA', False
        if prefix == 'ALT':
            return 'ALMACÉN TEMPORAL DE PRODUCTO TERMINADO', False
        if prefix == 'ALP':
            return 'ALMACÉN DE PRODUCTO TERMINADO', False
        if prefix == 'PRO':
            if family in ('AGO', 'HOR'):
                return 'LECTURA Y SECADO', False
            if family in ('BOM',):
                return 'INYECCIÓN', False
            return 'SOLUCIONES', False
        if prefix == 'VAL':
            return 'CONTROL DE CALIDAD', 'Prefijo VAL no existe como area en Odoo; confirmar si debe ser Validacion o Control de Calidad.'
        return False, 'No se pudo sugerir area desde el codigo.'

    def _find_pno_candidates(self):
        Procedure = self.env['amunet.quality.procedure'].sudo()
        all_procs = Procedure.search([('active', '=', True)])
        candidates = Procedure.browse()
        terms = self._search_terms()
        for proc in all_procs:
            haystack = ' '.join([
                proc.code or '',
                proc.name or '',
                proc.description or '',
            ]).lower()
            if any(term in haystack for term in terms):
                candidates |= proc
        return candidates[:12]

    def _search_terms(self):
        text = ' '.join([
            self.fva_equipment_name or '',
            self.identification_code or '',
            self.equipment_family or '',
        ]).lower()
        aliases = {
            'agi': ['agitador'],
            'ago': ['agitador', 'orbital'],
            'bal': ['balanza'],
            'bom': ['manometro', 'manómetro', 'bomba', 'compresor'],
            'cen': ['centrifuga', 'centrífuga'],
            'cgr': ['congelador'],
            'cnm': ['cronometro', 'cronómetro'],
            'esp': ['espectrofotometro', 'espectrofotómetro'],
            'fue': ['fuente de poder'],
            'hor': ['horno'],
            'mic': ['micropipeta', 'pipeta'],
            'ter': ['termohigrometro', 'termohigrómetro'],
            'dtl': ['data logger'],
            'ref': ['refrigerador'],
        }
        terms = []
        for token in re.findall(r'[a-záéíóúñü]+', text):
            if len(token) >= 4:
                terms.append(token)
        terms.extend(aliases.get((self.equipment_family or '').lower(), []))
        return list(dict.fromkeys(terms))

    def action_reconcile(self):
        _check_equipment_manager(self.env)
        Equipment = self.env['amunet.equipment'].sudo()
        for line in self:
            equipment = Equipment.search([
                ('serial_number', '=', line.identification_code)
            ], limit=1)
            department, dept_note = line._suggest_department(equipment)
            pno_candidates = line._find_pno_candidates()
            notes = []
            match_state = 'missing'
            if equipment:
                match_state = 'matched'
                if line.parsed_model and equipment.model_name:
                    if line.parsed_model.lower() not in equipment.model_name.lower():
                        match_state = 'mismatch'
                        notes.append('Modelo FVA "%s" vs Odoo "%s".' % (
                            line.parsed_model, equipment.model_name))
                if line.parsed_brand and equipment.brand:
                    if line.parsed_brand.lower() not in equipment.brand.lower():
                        match_state = 'mismatch'
                        notes.append('Marca FVA "%s" vs Odoo "%s".' % (
                            line.parsed_brand, equipment.brand))
            elif line.program_status == 'na':
                match_state = 'missing'
                notes.append('El programa indica NA; revisar si debe crearse equipo informativo.')
            line.write({
                'equipment_id': equipment.id if equipment else False,
                'match_state': match_state,
                'department_suggested': department,
                'department_final': line.department_final or department,
                'department_review_note': dept_note,
                'pno_candidate_ids': [(6, 0, pno_candidates.ids)],
                'mismatch_notes': '\n'.join(notes),
                'review_state': 'no_apply' if line.program_status == 'na' else 'pending',
                'requires_calibration': line.program_status != 'na',
            })
        return True

    def action_use_candidate_pnos(self):
        _check_equipment_manager(self.env)
        for line in self:
            line.pno_approved_ids = [(6, 0, line.pno_candidate_ids.ids)]
        return True

    def action_approve_line(self):
        _check_equipment_manager(self.env)
        for line in self:
            if line.program_status == 'na':
                line.review_state = 'no_apply'
                continue
            if not line.department_final:
                raise UserError(
                    "Define el area aprobada antes de aprobar %s."
                    % line.identification_code)
            line.review_state = 'approved'
        return True

    def action_apply_to_equipment(self):
        _check_equipment_manager(self.env)
        Equipment = self.env['amunet.equipment'].sudo()
        for line in self:
            if line.review_state != 'approved':
                continue
            vals = {
                'name': line.fva_equipment_name,
                'serial_number': line.identification_code,
                'brand': line.parsed_brand or False,
                'model_name': line.parsed_model or False,
                'department': line.department_final,
                'calibration_required': line.requires_calibration,
            }
            equipment = line.equipment_id
            if equipment:
                equipment.write({
                    key: value for key, value in vals.items()
                    if value or key == 'calibration_required'
                })
            else:
                vals['state'] = 'maintenance' if line.requires_calibration else 'active'
                equipment = Equipment.create(vals)
                line.equipment_id = equipment
            if line.pno_approved_ids:
                equipment.procedure_ids = [(4, p.id) for p in line.pno_approved_ids]
            line.review_state = 'applied'
            line.match_state = 'matched'
            line.message_post(body='Configuracion aplicada al equipo %s.' % equipment.display_name)
        return True
