# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError

SUPERVISOR_GROUP = 'amunet_bitacoras.group_bitacora_supervisor'

FREQ_SELECTION = [
    ('turno', 'Por turno'),
    ('diaria', 'Diaria'),
    ('semanal', 'Semanal'),
    ('quincenal', 'Quincenal'),
    ('mensual', 'Mensual'),
]

TIPO_SELECTION = [
    ('limpieza', 'Limpieza de área'),
    ('temp_humedad', 'Temperatura y humedad'),
    ('otro', 'Otro registro'),
]


class AmunetBitacoraTemplate(models.Model):
    _name = 'amunet.bitacora.template'
    _description = 'Plantilla de Bitácora (versionada y aprobada)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code, version desc'

    name = fields.Char(string='Nombre', required=True, tracking=True)
    code = fields.Char(string='Código', required=True, index=True, tracking=True)
    version = fields.Integer(string='Versión', default=1, required=True, tracking=True)
    tipo = fields.Selection(TIPO_SELECTION, string='Tipo', required=True, default='limpieza', tracking=True)

    area_id = fields.Many2one(
        'amunet.equipment.area', string='Área', tracking=True,
        help='Área física donde aplica esta bitácora.')
    department = fields.Char(string='Departamento (texto)', tracking=True)

    document_id = fields.Many2one(
        'amunet.documento', string='PNO / Documento controlado',
        help='Documento controlado (PNO) que rige esta bitácora.')
    pno_code = fields.Char(string='Código PNO', tracking=True)
    formato_code = fields.Char(string='Código de formato', tracking=True)

    frecuencia = fields.Selection(FREQ_SELECTION, string='Frecuencia', required=True, default='diaria', tracking=True)
    shift_count = fields.Integer(
        string='Turnos por día', default=1, tracking=True,
        help='Solo aplica cuando la frecuencia es "Por turno". Número de registros por día.')
    tolerance_hours = fields.Integer(
        string='Tolerancia (horas)', default=24,
        help='Horas tras la fecha programada antes de marcar el registro como omitido.')

    # Límites de especificación (temperatura y humedad)
    temp_min = fields.Float(string='Temp. mínima (°C)')
    temp_max = fields.Float(string='Temp. máxima (°C)')
    hum_min = fields.Float(string='Humedad mínima (%HR)')
    hum_max = fields.Float(string='Humedad máxima (%HR)')

    requires_confirmation = fields.Boolean(
        string='Pendiente de confirmar datos', default=False, tracking=True,
        help='Marca que los límites/áreas fueron sembrados por defecto y deben confirmarse antes de activar.')

    checklist_item_ids = fields.One2many(
        'amunet.bitacora.checklist.item', 'template_id', string='Pasos de la bitácora')

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('approved', 'Aprobada'),
        ('active', 'Activa'),
        ('archived', 'Archivada'),
    ], string='Estado', default='draft', required=True, tracking=True)

    approved_by = fields.Many2one('res.users', string='Aprobada por', readonly=True)
    approved_on = fields.Datetime(string='Fecha de aprobación', readonly=True)

    active = fields.Boolean(default=True)
    notes = fields.Text(string='Notas')

    entry_count = fields.Integer(compute='_compute_entry_count', string='Registros')

    _code_version_uniq = models.Constraint(
        'unique(code, version)',
        'Ya existe una plantilla con ese código y versión.',
    )

    # Campos que definen la "receta" regulada; no se editan tras aprobar (control de cambios).
    CRITICAL_FIELDS = {
        'code', 'tipo', 'area_id', 'department', 'frecuencia', 'shift_count',
        'temp_min', 'temp_max', 'hum_min', 'hum_max', 'document_id', 'pno_code',
        'formato_code', 'version', 'tolerance_hours',
    }

    def write(self, vals):
        # Bloquea campos críticos en plantillas no-borrador, incluso si el write
        # también trae 'state' (evita bypass al incluir state en el mismo write).
        for rec in self:
            if rec.state in ('approved', 'active', 'archived'):
                illegal = self.CRITICAL_FIELDS.intersection(vals.keys())
                if illegal:
                    raise UserError(_(
                        'La plantilla "%s" está %s. Para cambiar %s crea una nueva revisión '
                        '(botón "Nueva revisión").'
                    ) % (rec.name, rec.state, ', '.join(sorted(illegal))))
        return super().write(vals)

    def _compute_entry_count(self):
        data = self.env['amunet.bitacora.entry']._read_group(
            [('template_id', 'in', self.ids)], ['template_id'], ['__count'])
        mapped = {t.id: c for t, c in data}
        for rec in self:
            rec.entry_count = mapped.get(rec.id, 0)

    @api.constrains('tipo', 'temp_min', 'temp_max', 'hum_min', 'hum_max', 'state')
    def _check_limits(self):
        for rec in self:
            if rec.state in ('approved', 'active') and rec.tipo == 'temp_humedad':
                if rec.temp_max <= rec.temp_min and not (rec.temp_min == 0 and rec.temp_max == 0):
                    raise ValidationError(_('La temperatura máxima debe ser mayor que la mínima.'))
                if rec.hum_max <= rec.hum_min and not (rec.hum_min == 0 and rec.hum_max == 0):
                    raise ValidationError(_('La humedad máxima debe ser mayor que la mínima.'))

    def _check_supervisor(self):
        if not self.env.su and not self.env.user.has_group(SUPERVISOR_GROUP):
            raise AccessError(_('Solo un supervisor de bitácoras puede cambiar el estado de la plantilla.'))

    def action_approve(self):
        self._check_supervisor()
        for rec in self:
            if rec.requires_confirmation:
                raise UserError(_(
                    'La plantilla "%s" tiene datos sembrados por defecto pendientes de confirmar. '
                    'Desmarca "Pendiente de confirmar datos" tras revisar áreas y límites.') % rec.name)
            if rec.tipo == 'temp_humedad' and not (rec.temp_max > rec.temp_min):
                raise UserError(_('Define límites de temperatura válidos antes de aprobar "%s".') % rec.name)
            rec.write({
                'state': 'approved',
                'approved_by': self.env.user.id,
                'approved_on': fields.Datetime.now(),
            })
            rec.message_post(body=_('Plantilla aprobada (versión %s).') % rec.version)

    def action_activate(self):
        self._check_supervisor()
        for rec in self:
            if rec.state != 'approved':
                raise UserError(_('Solo se pueden activar plantillas aprobadas.'))
            # Archivar versiones activas previas del mismo código
            previous = self.search([
                ('code', '=', rec.code), ('state', '=', 'active'), ('id', '!=', rec.id)])
            previous.write({'state': 'archived'})
            rec.state = 'active'
            rec.message_post(body=_('Plantilla activada. Versiones previas archivadas: %s.') % len(previous))

    def action_archive_template(self):
        self._check_supervisor()
        self.write({'state': 'archived'})

    def action_new_revision(self):
        """Crea una nueva revisión en borrador a partir de la activa (control de cambios)."""
        self._check_supervisor()
        self.ensure_one()
        new = self.copy({
            'version': self.version + 1,
            'state': 'draft',
            'approved_by': False,
            'approved_on': False,
        })
        new.message_post(body=_('Nueva revisión creada desde la versión %s.') % self.version)
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': new.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _due_periods(self, today):
        """Devuelve lista de (period_key, scheduled_date, shift) que deben existir hoy.

        Estrategia conservadora: genera el periodo correspondiente a la fecha de hoy
        según la frecuencia. El cron corre a diario; la unicidad evita duplicados.
        """
        self.ensure_one()
        from datetime import timedelta
        result = []
        freq = self.frecuencia
        if freq in ('diaria', 'turno'):
            key = today.strftime('%Y-%m-%d')
            shifts = self.shift_count if (freq == 'turno' and self.shift_count > 0) else 1
            for s in range(1, shifts + 1):
                result.append(('%s/D' % key, today, s))
        elif freq == 'semanal':
            # Periodo = semana ISO actual; fecha programada = lunes de la semana.
            iso_year, iso_week, iso_dow = today.isocalendar()
            monday = today - timedelta(days=iso_dow - 1)
            key = '%s-W%02d' % (iso_year, iso_week)
            result.append((key, monday, 1))
        elif freq == 'quincenal':
            half = '1' if today.day <= 15 else '2'
            sched = today.replace(day=1) if half == '1' else today.replace(day=16)
            key = today.strftime('%Y-%m-Q') + half
            result.append((key, sched, 1))
        elif freq == 'mensual':
            key = today.strftime('%Y-%m')
            result.append((key, today.replace(day=1), 1))
        return result

    def action_view_entries(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Registros de %s') % self.name,
            'res_model': 'amunet.bitacora.entry',
            'view_mode': 'list,form',
            'domain': [('template_id', '=', self.id)],
            'context': {'default_template_id': self.id},
        }


class AmunetBitacoraChecklistItem(models.Model):
    _name = 'amunet.bitacora.checklist.item'
    _description = 'Paso de bitácora (plantilla)'
    _order = 'sequence, id'

    template_id = fields.Many2one(
        'amunet.bitacora.template', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Paso / punto a verificar', required=True)
    required = fields.Boolean(string='Obligatorio', default=True)

    def _check_template_draft(self):
        for rec in self:
            if rec.template_id.state not in ('draft',) and not self.env.context.get('install_mode'):
                raise UserError(_(
                    'No se pueden cambiar los pasos de una plantilla aprobada. '
                    'Crea una nueva revisión.'))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get('install_mode'):
            for rec in records:
                if rec.template_id.state not in ('draft',):
                    raise UserError(_(
                        'No se pueden agregar pasos a una plantilla aprobada. '
                        'Crea una nueva revisión.'))
        return records

    def write(self, vals):
        self._check_template_draft()
        return super().write(vals)

    def unlink(self):
        self._check_template_draft()
        return super().unlink()
