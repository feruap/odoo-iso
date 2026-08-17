from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_TIPO = [
    ('P', 'P'),
    ('NP', 'NP'),
    ('AR', 'AR'),
]

_AREA = [
    ('GE', 'Generales'),
    ('AD', 'Administracion'),
    ('MA', 'Mantenimiento'),
    ('TV', 'Tecnovigilancia'),
    ('DC', 'Documentacion'),
    ('PR', 'Produccion'),
    ('CC', 'Control de Calidad'),
    ('EST', 'Estabilidad'),
    ('AS', 'Aseguramiento de Calidad'),
    ('AL', 'Almacen'),
    ('IN', 'Ingenieria'),
    ('RH', 'Recursos Humanos'),
    ('OTRO', 'Otra'),
]


class AmunetProgramaAuditoria(models.Model):
    _name = 'amunet.programa.auditoria'
    _description = 'Programa Anual de Auditorías'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'anio desc'
    _rec_name = 'name'

    name = fields.Char(compute='_compute_name', store=True)
    anio = fields.Integer(
        string='Año', required=True,
        default=lambda self: fields.Date.today().year)
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('vigente', 'Vigente'),
        ('cerrado', 'Cerrado'),
    ], default='borrador', string='Estado', required=True)

    linea_ids = fields.One2many(
        'amunet.programa.auditoria.linea', 'programa_id', string='Alcances')
    alcance_count = fields.Integer(
        compute='_compute_alcance_count', string='Núm. alcances')

    observaciones = fields.Text()

    elaboro_id = fields.Many2one('res.users', string='Elaboró', readonly=True)
    fecha_elaboracion = fields.Date(string='Fecha elaboración', readonly=True)
    autorizo_id = fields.Many2one('res.users', string='Autorizó', readonly=True)
    fecha_autorizacion = fields.Date(string='Fecha autorización', readonly=True)

    @api.depends('anio')
    def _compute_name(self):
        for r in self:
            r.name = 'Programa de Auditorías %s' % (r.anio or '')

    def _compute_alcance_count(self):
        for r in self:
            r.alcance_count = len(r.linea_ids)

    # ── Firma electrónica ──────────────────────────────────────────────────

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_elaborar': _('Elaboración del programa anual de auditorías'),
            '_signature_autorizar': _('Autorización del programa anual de auditorías'),
        }

    def action_firmar_elaboracion(self):
        self.ensure_one()
        if self.state != 'borrador':
            raise ValidationError(_('Solo se puede firmar la elaboración en estado Borrador.'))
        return self.env['amunet.generic.signature.wizard'].open_for(
            self,
            '_signature_elaborar',
            _('Elaboró'),
            _('Firma de elaboración del %s.') % self.name,
        )

    def _signature_elaborar(self):
        self.ensure_one()
        self.with_context(_skip_signature_check=True).write({
            'elaboro_id': self.env.user.id,
            'fecha_elaboracion': fields.Date.today(),
        })
        return True

    def action_firmar_autorizacion(self):
        self.ensure_one()
        if self.state not in ('borrador', 'vigente'):
            raise ValidationError(_('No se puede firmar la autorización en este estado.'))
        if not self.elaboro_id:
            raise ValidationError(_('Firma primero la elaboración antes de autorizar.'))
        return self.env['amunet.generic.signature.wizard'].open_for(
            self,
            '_signature_autorizar',
            _('Autorizó'),
            _('Firma de autorización del %s.') % self.name,
        )

    def _signature_autorizar(self):
        self.ensure_one()
        self.with_context(_skip_signature_check=True).write({
            'autorizo_id': self.env.user.id,
            'fecha_autorizacion': fields.Date.today(),
            'state': 'vigente',
        })
        return True

    # ── Acciones de estado ─────────────────────────────────────────────────

    def action_reprogramar(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reprogramar'),
            'res_model': 'amunet.programa.reprogramar.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_programa_id': self.id},
        }

    def action_cerrar(self):
        self.write({'state': 'cerrado'})

    def action_borrador(self):
        self.write({'state': 'borrador', 'autorizo_id': False, 'fecha_autorizacion': False})


class AmunetProgramaAuditoriaLinea(models.Model):
    _name = 'amunet.programa.auditoria.linea'
    _description = 'Línea del programa anual de auditorías'
    _order = 'programa_id, secuencia, id'

    programa_id = fields.Many2one(
        'amunet.programa.auditoria', required=True, ondelete='cascade')
    secuencia = fields.Integer(default=10)
    alcance = fields.Selection(_AREA, string='Área', required=True)
    supervisor_id = fields.Many2one(
        'res.users', string='Supervisor',
        domain=[('share', '=', False), ('active', '=', True)])

    ene = fields.Selection(_TIPO, string='ENE')
    feb = fields.Selection(_TIPO, string='FEB')
    mar = fields.Selection(_TIPO, string='MAR')
    abr = fields.Selection(_TIPO, string='ABR')
    may = fields.Selection(_TIPO, string='MAY')
    jun = fields.Selection(_TIPO, string='JUN')
    jul = fields.Selection(_TIPO, string='JUL')
    ago = fields.Selection(_TIPO, string='AGO')
    sep = fields.Selection(_TIPO, string='SEP')
    oct = fields.Selection(_TIPO, string='OCT')
    nov = fields.Selection(_TIPO, string='NOV')
    dic = fields.Selection(_TIPO, string='DIC')
