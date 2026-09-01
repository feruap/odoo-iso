from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_RESPUESTA = [
    ('2', '2 — Cumple'),
    ('1', '1 — Parcial'),
    ('0', '0 — No cumple'),
    ('na', 'N/A'),
]

_SECCIONES = [
    ('cumplimiento_legal', 'Cumplimiento Legal'),
    ('capacidad_area', 'Capacidad del Área'),
    ('desempeno_area', 'Desempeño del Área'),
    ('personal', 'Personal'),
]


class AmunetListaVerificacion(models.Model):
    _name = 'amunet.lista.verificacion'
    _description = 'Lista de Verificación de Auditoría'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'clave'
    _order = 'fecha desc, id'

    clave = fields.Char(string='Clave', readonly=True, copy=False,
        default=lambda self: _('Nuevo'))
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('firmado', 'Firmado'),
    ], default='borrador', string='Estado', tracking=True)

    # ── Vinculación al plan ────────────────────────────────────────────────
    plan_id = fields.Many2one('amunet.plan.auditoria', string='Plan de auditoría',
        required=True, domain=[('state', '=', 'emitido')])

    no_auditoria = fields.Char(related='plan_id.clave', string='No. Auditoría', store=True)
    fecha = fields.Date(related='plan_id.fecha_inicio', string='Fecha', store=True)
    lider_id = fields.Many2one(related='plan_id.lider_id', string='Auditor líder', store=True)

    # Datos propios
    area_proceso = fields.Char(string='Área / Proceso auditado')
    supervisor_id = fields.Many2one('res.users', string='Supervisor del área',
        domain=[('share', '=', False)])

    # ── Ítems por sección ─────────────────────────────────────────────────
    item_legal_ids = fields.One2many('amunet.lista.verificacion.item', 'lista_id',
        domain=[('seccion', '=', 'cumplimiento_legal')], string='Cumplimiento Legal')
    item_capacidad_ids = fields.One2many('amunet.lista.verificacion.item', 'lista_id',
        domain=[('seccion', '=', 'capacidad_area')], string='Capacidad del Área')
    item_desempeno_ids = fields.One2many('amunet.lista.verificacion.item', 'lista_id',
        domain=[('seccion', '=', 'desempeno_area')], string='Desempeño del Área')
    item_personal_ids = fields.One2many('amunet.lista.verificacion.item', 'lista_id',
        domain=[('seccion', '=', 'personal')], string='Personal')

    puntos_fijos = fields.Boolean(string='Puntos fijos', default=False)

    # ── Cierre ────────────────────────────────────────────────────────────
    observaciones_generales = fields.Text(string='Observaciones generales')
    resultado = fields.Text(string='Resultado')

    # ── Firmas ────────────────────────────────────────────────────────────
    firma_supervisor_id = fields.Many2one('res.users', string='Supervisor', readonly=True)
    fecha_firma_supervisor = fields.Date(string='Fecha', readonly=True)
    firma_auditor_id = fields.Many2one('res.users', string='Auditor', readonly=True)
    fecha_firma_auditor = fields.Date(string='Fecha', readonly=True)

    puede_firmar_supervisor = fields.Boolean(compute='_compute_puede_firmar_supervisor')

    def _compute_puede_firmar_supervisor(self):
        uid = self.env.user.id
        for r in self:
            r.puede_firmar_supervisor = (
                uid == r.supervisor_id.id and not r.firma_supervisor_id
            )

    # ── Secuencia ─────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('clave', _('Nuevo')) == _('Nuevo'):
                hoy = fields.Date.context_today(self)
                mm = hoy.strftime('%m')
                yy = hoy.strftime('%y')
                num = self.env['ir.sequence'].next_by_code('amunet.lista.verificacion') or '001'
                vals['clave'] = f'LV{mm}{yy}-{num}'
        return super().create(vals_list)

    # ── Firma electrónica ─────────────────────────────────────────────────

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_supervisor': _('Firma del Supervisor del área auditada'),
            '_signature_auditor': _('Firma del Auditor (Amunet)'),
        }

    def action_firmar_supervisor(self):
        self.ensure_one()
        uid = self.env.user.id
        if self.supervisor_id and uid != self.supervisor_id.id:
            raise ValidationError(_('Solo el supervisor del área puede firmar aquí.'))
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_supervisor',
            _('Supervisor del área'),
            _('Firma del supervisor — lista %s.') % self.clave,
        )

    def _signature_supervisor(self):
        self.ensure_one()
        self.write({
            'firma_supervisor_id': self.env.user.id,
            'fecha_firma_supervisor': fields.Date.today(),
        })
        return {'type': 'ir.actions.act_window_close'}

    def action_firmar_auditor(self):
        self.ensure_one()
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_auditor',
            _('Auditor (Amunet)'),
            _('Firma del auditor — lista %s.') % self.clave,
        )

    def _signature_auditor(self):
        self.ensure_one()
        self.write({
            'firma_auditor_id': self.env.user.id,
            'fecha_firma_auditor': fields.Date.today(),
            'state': 'firmado',
        })
        return {'type': 'ir.actions.act_window_close'}

    def action_fijar_puntos(self):
        self.ensure_one()
        self.puntos_fijos = True

    def action_desbloquear_puntos(self):
        self.ensure_one()
        self.puntos_fijos = False

    def action_borrador(self):
        self.write({
            'state': 'borrador',
            'puntos_fijos': False,
            'firma_supervisor_id': False, 'fecha_firma_supervisor': False,
            'firma_auditor_id': False, 'fecha_firma_auditor': False,
        })


class AmunetListaVerificacionItem(models.Model):
    _name = 'amunet.lista.verificacion.item'
    _description = 'Punto de verificación'
    _order = 'lista_id, seccion, sequence, id'

    lista_id = fields.Many2one('amunet.lista.verificacion', required=True, ondelete='cascade')
    seccion = fields.Selection(_SECCIONES, required=True)
    sequence = fields.Integer(default=10)
    punto = fields.Char(string='Punto a evaluar', required=True)
    respuesta = fields.Selection(_RESPUESTA, string='Respuesta')
    observaciones = fields.Char(string='Observaciones')
