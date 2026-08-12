from odoo import models, fields, api
from odoo.exceptions import UserError

CUMPLE = [('cumple', '✓'), ('no_cumple', '✗'), ('na', 'N/A')]


class AmunetRegRevisionVest(models.Model):
    _name = 'amunet.reg.revision.vest'
    _description = 'Revisión de Indumentaria (F-GE-007/002)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha desc, id desc'

    name = fields.Char(string='Folio', readonly=True, copy=False, default='Nuevo')
    fecha = fields.Date(string='Fecha', default=fields.Date.today, required=True, tracking=True)
    turno = fields.Selection([
        ('matutino', 'Matutino'),
        ('vespertino', 'Vespertino'),
        ('nocturno', 'Nocturno'),
    ], string='Turno', required=True, tracking=True)
    responsable_id = fields.Many2one(
        'res.users', string='Revisó',
        default=lambda self: self.env.user, tracking=True)
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('cerrado', 'Cerrado'),
    ], default='borrador', string='Estado', tracking=True)
    linea_ids = fields.One2many(
        'amunet.reg.revision.vest.linea', 'registro_id', string='Revisiones')

    firma_id = fields.Many2one('res.users', string='Firmó', readonly=True)
    fecha_firma = fields.Datetime(string='Fecha de firma', readonly=True)

    total_revisados = fields.Integer(compute='_compute_totales', store=True)
    total_no_cumple = fields.Integer(
        string='Con incidencia', compute='_compute_totales', store=True)

    @api.depends('linea_ids', 'linea_ids.tiene_incidencia')
    def _compute_totales(self):
        for rec in self:
            rec.total_revisados = len(rec.linea_ids)
            rec.total_no_cumple = len(rec.linea_ids.filtered('tiene_incidencia'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'amunet.reg.revision.vest') or 'Nuevo'
        return super().create(vals_list)

    def action_cerrar(self):
        for rec in self:
            if not rec.linea_ids:
                raise UserError('Agrega al menos un registro antes de cerrar.')
            rec.write({'state': 'cerrado'})

    def action_reabrir(self):
        self.write({'state': 'borrador'})

    def _amunet_signature_allowed_methods(self):
        return {'action_firmar_revisor': 'Firma del revisor'}

    def action_firmar_revisor(self):
        self.write({
            'firma_id': self.env.user.id,
            'fecha_firma': fields.Datetime.now(),
        })


class AmunetRegRevisionVestLinea(models.Model):
    _name = 'amunet.reg.revision.vest.linea'
    _description = 'Línea — Revisión de Indumentaria'
    _order = 'sequence, id'

    registro_id = fields.Many2one(
        'amunet.reg.revision.vest', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    empleado_nombre = fields.Char(string='Nombre', required=True)

    gafete = fields.Selection(CUMPLE, string='Gafete')
    filipina_bata = fields.Selection(CUMPLE, string='Filipina / Bata')
    zapato = fields.Selection(CUMPLE, string='Zapato')
    unas = fields.Selection(CUMPLE, string='Uñas')
    maquillaje = fields.Selection(CUMPLE, string='Maquillaje')
    accesorios = fields.Selection(CUMPLE, string='Accesorios')
    observaciones = fields.Char(string='Observaciones')

    tiene_incidencia = fields.Boolean(compute='_compute_incidencia', store=True)

    @api.depends('gafete', 'filipina_bata', 'zapato', 'unas', 'maquillaje', 'accesorios')
    def _compute_incidencia(self):
        campos = ['gafete', 'filipina_bata', 'zapato', 'unas', 'maquillaje', 'accesorios']
        for rec in self:
            rec.tiene_incidencia = any(
                getattr(rec, c) == 'no_cumple' for c in campos)
