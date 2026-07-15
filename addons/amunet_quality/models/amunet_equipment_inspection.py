# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class AmunetEquipmentInspection(models.Model):
    _name = 'amunet.equipment.inspection'
    _description = 'Inspección de Equipos Entrantes'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(
        string='Referencia', readonly=True, copy=False, default='Nuevo')

    analysis_number = fields.Char(
        string='No. de análisis', readonly=True, copy=False, tracking=True)

    analysis_number_preview = fields.Char(
        string='Vista previa del No. de análisis',
        compute='_compute_analysis_number_preview')

    state = fields.Selection([
        ('draft', 'Por realizar'),
        ('in_progress', 'En proceso'),
        ('done', 'Finalizado'),
    ], string='Estado', default='draft', required=True, tracking=True)

    equipment_type = fields.Selection([
        ('termobloque',         'Termobloque'),
        ('vortex',              'Vórtex'),
        ('micropipeta_pequena', 'Micropipeta 5–50 µL'),
        ('micropipeta_grande',  'Micropipeta 100–1000 µL'),
        ('centrifuga',          'Centrífuga'),
        ('incubadora',          'Incubadora'),
        ('gradilla',            'Gradilla'),
        ('soporte_pipetas',     'Soporte para micropipetas'),
        ('otro',                'Otro'),
    ], string='Tipo de equipo', required=True, tracking=True)

    equipment_model = fields.Char(string='Modelo', tracking=True,
        help='Ej: MB100, DB100, MDB100')

    equipment_code = fields.Char(string='Clave', tracking=True,
        help='Ej: EQTER01, EQVOR01')

    lot_amunet = fields.Char(string='Lote Amunet', tracking=True,
        help='Lote interno asignado al recibir el equipo')

    lot_approved = fields.Char(string='Lote aprobados', tracking=True,
        help='Lote Amunet para los equipos que cumplieron')

    lot_rejected = fields.Char(string='Lote rechazados', tracking=True,
        help='Lote Amunet para los equipos rechazados (se genera automáticamente)')

    entry_date = fields.Date(string='Fecha de entrada', tracking=True)
    analysis_date = fields.Date(string='Fecha de análisis', tracking=True)
    quantity_received = fields.Float(string='Cantidad recibida', digits=(10, 0))

    line_ids = fields.One2many(
        'amunet.equipment.inspection.line', 'inspection_id',
        string='Números de serie')

    notes = fields.Text(string='Observaciones generales')

    # Firmas
    user_realized_id = fields.Many2one(
        'res.users', string='Realizó', readonly=True, tracking=True)
    sign_realized_date = fields.Datetime(string='Fecha firma Realizó', readonly=True)

    user_verified_id = fields.Many2one(
        'res.users', string='Verificó', readonly=True, tracking=True)
    sign_verified_date = fields.Datetime(string='Fecha firma Verificó', readonly=True)

    # Conteos computados
    approved_count = fields.Integer(
        string='Aprobados', compute='_compute_counts', store=True)
    rejected_count = fields.Integer(
        string='Rechazados', compute='_compute_counts', store=True)

    @api.depends('line_ids.status')
    def _compute_counts(self):
        for rec in self:
            rec.approved_count = sum(1 for l in rec.line_ids if l.status == 'approved')
            rec.rejected_count = sum(1 for l in rec.line_ids if l.status == 'rejected')

    @api.depends('user_realized_id', 'state')
    def _compute_analysis_number_preview(self):
        for rec in self:
            if rec.analysis_number:
                rec.analysis_number_preview = rec.analysis_number
            elif rec.user_realized_id:
                code = getattr(rec.user_realized_id, 'employee_code', None) or '000'
                import datetime
                today = datetime.date.today()
                date_str = today.strftime('%d%m%y')
                rec.analysis_number_preview = f'{code}{date_str}-NN'
            else:
                rec.analysis_number_preview = ''

    def _generate_analysis_number(self):
        self.ensure_one()
        if not self.user_realized_id:
            raise ValidationError('Debe registrar quién realizó el análisis antes de finalizar.')
        employee_code = getattr(self.user_realized_id, 'employee_code', None) or '000'
        today = fields.Date.today()
        date_str = today.strftime('%d%m%y')
        prefix = f'{employee_code}{date_str}'
        last = self.search([
            ('analysis_number', 'like', f'{prefix}%'),
            ('id', '!=', self.id),
        ], order='analysis_number desc', limit=1)
        if last and last.analysis_number:
            try:
                seq = int(last.analysis_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f'{prefix}-{seq:02d}'

    def _get_lot_suffix(self):
        """Genera sufijo para el lote rechazado: lote_aprobado + 1."""
        base = (self.lot_amunet or '').rstrip('0123456789')
        num = (self.lot_amunet or '')[-2:]
        try:
            return f'{base}{int(num) + 1:02d}'
        except ValueError:
            return f'{self.lot_amunet or ""}02'

    def action_start(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError('Solo se puede iniciar una hoja en estado Borrador.')
        seq = self.env['ir.sequence'].next_by_code('amunet.equipment.inspection')
        self.write({'name': seq, 'state': 'in_progress'})

    def action_sign_realized(self):
        self.ensure_one()
        if self.user_realized_id:
            raise UserError('La firma de "Realizó" ya fue registrada.')
        self.write({
            'user_realized_id': self.env.user.id,
            'sign_realized_date': fields.Datetime.now(),
        })

    def action_sign_verified(self):
        self.ensure_one()
        if not self.user_realized_id:
            raise UserError('Debe registrar primero la firma de "Realizó".')
        if self.user_verified_id:
            raise UserError('La firma de "Verificó" ya fue registrada.')
        self.write({
            'user_verified_id': self.env.user.id,
            'sign_verified_date': fields.Datetime.now(),
        })

    def action_finalize(self):
        self.ensure_one()
        if not self.user_realized_id or not self.user_verified_id:
            raise UserError('Se requieren ambas firmas (Realizó y Verificó) para finalizar.')
        if not self.line_ids:
            raise UserError('Debe registrar al menos un número de serie antes de finalizar.')

        analysis_number = self._generate_analysis_number()

        # Lote de rechazados automático si hay rechazados
        lot_rejected = False
        if self.rejected_count > 0 and not self.lot_rejected:
            lot_rejected = self._get_lot_suffix()

        vals = {
            'state': 'done',
            'analysis_number': analysis_number,
            'analysis_date': fields.Date.today(),
        }
        if lot_rejected:
            vals['lot_rejected'] = lot_rejected

        self.write(vals)

        # Notificar a almacén (Karla)
        self._notify_almacen()

        return True

    def _notify_almacen(self):
        """Envía mensaje al chatter y correo a Karla con el resultado."""
        approved_serials = self.line_ids.filtered(
            lambda l: l.status == 'approved').mapped('serial_number')
        rejected_serials = self.line_ids.filtered(
            lambda l: l.status == 'rejected').mapped('serial_number')

        body = f"""
<p><strong>Inspección de equipos completada — {self.name}</strong></p>
<p>Tipo: {dict(self._fields['equipment_type'].selection).get(self.equipment_type, '')}
{(' — Modelo: ' + self.equipment_model) if self.equipment_model else ''}
{(' — Clave: ' + self.equipment_code) if self.equipment_code else ''}</p>
<p>Lote Amunet: {self.lot_amunet or '-'} | No. de análisis: {self.analysis_number}</p>
<p><strong>Aprobados ({self.approved_count}):</strong> {', '.join(approved_serials) or 'Ninguno'}</p>
<p><strong>Rechazados ({self.rejected_count}):</strong> {', '.join(rejected_serials) or 'Ninguno'}
{(' — Lote rechazados: ' + self.lot_rejected) if self.lot_rejected else ''}</p>
<p>Por favor realiza la separación de lotes en inventario. Gracias.</p>
"""
        # Notificación interna en el chatter — avisa a Karla y Verónica
        partners = self.env['res.partner'].search([
            ('email', 'in', ['almacen.mp@amunet.com.mx', 'supalmacen@amunet.com.mx'])
        ])
        self.message_post(
            body=body,
            subject=f'Inspección {self.name} finalizada — acción requerida en almacén',
            partner_ids=partners.ids,
        )

    def action_print_approved(self):
        return self.env.ref(
            'amunet_quality.action_report_equipment_inspection_approved'
        ).report_action(self)

    def action_print_rejected(self):
        return self.env.ref(
            'amunet_quality.action_report_equipment_inspection_rejected'
        ).report_action(self)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'amunet.equipment.inspection') or 'Nuevo'
        return super().create(vals_list)


class AmunetEquipmentInspectionLine(models.Model):
    _name = 'amunet.equipment.inspection.line'
    _description = 'Línea de Inspección de Equipo'
    _order = 'sequence, id'

    inspection_id = fields.Many2one(
        'amunet.equipment.inspection', string='Inspección',
        required=True, ondelete='cascade')

    sequence = fields.Integer(string='Sec.', default=10)

    serial_number = fields.Char(string='No. de serie / Lote', required=True)

    status = fields.Selection([
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
    ], string='Estatus', required=True, default='approved')

    observations = fields.Text(string='Observaciones')
