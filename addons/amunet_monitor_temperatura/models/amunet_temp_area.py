# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


def fmt_hour12(hour):
    """Formatea una hora float (24h) a texto de 12 horas con AM/PM.
    9.0 -> '9:00 AM', 13.0 -> '1:00 PM', 17.75 -> '5:45 PM'."""
    hour = hour or 0.0
    hh = int(hour)
    mm = int(round((hour - hh) * 60))
    if mm == 60:
        hh += 1
        mm = 0
    ampm = 'AM' if hh < 12 else 'PM'
    h12 = hh % 12
    if h12 == 0:
        h12 = 12
    return '%d:%02d %s' % (h12, mm, ampm)


class AmunetTempArea(models.Model):
    _name = 'amunet.temp.area'
    _description = 'Area de monitoreo de temperatura'
    _order = 'sequence, name'

    name = fields.Char(string='Area', required=True)
    code = fields.Char(string='Codigo', index=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    # Departamento responsable: define quien captura y de donde sale el
    # supervisor. Todo se deriva de Empleados (puesto + departamento).
    responsible_department_id = fields.Many2one(
        'hr.department', string='Departamento responsable', required=True,
        help='Departamento del que salen los capturistas y el supervisor.')
    capture_pool = fields.Boolean(
        string='Captura cualquier integrante del area (subarbol)',
        help='Si esta activo, puede capturar cualquier persona del '
             'departamento responsable y de sus subdepartamentos '
             '(ej. cualquier operador de Produccion). Si no, solo el '
             'personal directo del departamento.')

    # Limites de especificacion
    temp_min = fields.Float(string='Temp. minima (C)', default=15.0)
    temp_max = fields.Float(string='Temp. maxima (C)', default=30.0)
    hum_required = fields.Boolean(string='Captura humedad', default=True)
    hum_min = fields.Float(string='Humedad minima (%HR)', default=0.0)
    hum_max = fields.Float(string='Humedad maxima (%HR)', default=65.0)

    # Programacion
    slot_ids = fields.One2many(
        'amunet.temp.slot', 'area_id', string='Horarios de captura')
    tolerance_minutes = fields.Integer(
        string='Tolerancia (min)', default=15,
        help='Minutos despues del horario antes de marcar No realizado.')

    # Instrumento(s) (termohigrometro) ligado(s) a su calibracion
    instrument_ids = fields.Many2many(
        'amunet.equipment', string='Termohigrometros',
        help='Equipos con los que se mide en esta area (su calibracion '
             'queda trazada en el modulo de calibracion). Un area puede '
             'tener mas de uno (ej. Estabilidad).')
    instrument_label = fields.Char(
        string='Termohigrometro(s)', compute='_compute_instrument_label')

    @api.depends('instrument_ids.serial_number', 'instrument_ids.name')
    def _compute_instrument_label(self):
        for area in self:
            area.instrument_label = ', '.join(
                e.serial_number or e.name for e in area.instrument_ids)

    # Derivados de Empleados (no almacenados)
    supervisor_user_id = fields.Many2one(
        'res.users', string='Supervisor (derivado)',
        compute='_compute_supervisor', store=False)
    capturer_user_ids = fields.Many2many(
        'res.users', string='Capturistas (derivado)',
        compute='_compute_capturers', store=False)

    # ------------------------------------------------------------------
    # Derivacion desde Empleados
    # ------------------------------------------------------------------
    def _amunet_capturer_users(self):
        self.ensure_one()
        dept = self.responsible_department_id
        if not dept:
            return self.env['res.users']
        Dept = self.env['hr.department'].sudo()
        if self.capture_pool:
            depts = Dept.search([('id', 'child_of', dept.id)])
        else:
            depts = dept
        emps = self.env['hr.employee'].sudo().search([
            ('department_id', 'in', depts.ids)])
        return emps.mapped('user_id')

    def _amunet_supervisor_user(self):
        self.ensure_one()
        Emp = self.env['hr.employee'].sudo()
        dept = self.responsible_department_id
        # busca el puesto 'Supervisor' en el depto; si no, sube al padre
        while dept:
            sup = Emp.search([
                ('department_id', '=', dept.id),
                ('job_id.name', 'ilike', 'supervisor'),
            ], limit=1)
            if sup and sup.user_id:
                return sup.user_id
            dept = dept.parent_id
        return self.env['res.users']

    @api.depends('responsible_department_id', 'capture_pool')
    def _compute_capturers(self):
        for area in self:
            area.capturer_user_ids = area._amunet_capturer_users()

    @api.depends('responsible_department_id')
    def _compute_supervisor(self):
        for area in self:
            area.supervisor_user_id = area._amunet_supervisor_user()

    def amunet_user_can_capture(self, user=None):
        self.ensure_one()
        user = user or self.env.user
        if user.has_group('amunet_monitor_temperatura.group_temp_manager'):
            return True
        return user in self._amunet_capturer_users()

    def amunet_user_is_supervisor(self, user=None):
        self.ensure_one()
        user = user or self.env.user
        if user.has_group('amunet_monitor_temperatura.group_temp_manager'):
            return True
        return user == self._amunet_supervisor_user()


class AmunetTempSlot(models.Model):
    _name = 'amunet.temp.slot'
    _description = 'Horario de captura de temperatura'
    _order = 'time_hour'

    area_id = fields.Many2one('amunet.temp.area', required=True, ondelete='cascade')
    time_hour = fields.Float(
        string='Hora (24h)', required=True,
        help='Hora programada del turno, formato 24h (ej. 9.0, 13.0, 18.0).')
    name = fields.Char(string='Etiqueta', compute='_compute_name', store=True)

    @api.depends('time_hour')
    def _compute_name(self):
        for s in self:
            s.name = fmt_hour12(s.time_hour)
