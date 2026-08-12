from odoo import models, fields, api
from odoo.exceptions import UserError


class AmunetRegEntregaVest(models.Model):
    _name = 'amunet.reg.entrega.vest'
    _description = 'Entrega de Indumentaria (F-GE-007/001)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha desc, id desc'

    name = fields.Char(string='Folio', readonly=True, copy=False, default='Nuevo')
    fecha = fields.Date(string='Fecha', default=fields.Date.today, required=True, tracking=True)
    responsable_id = fields.Many2one(
        'res.users', string='Entregó',
        default=lambda self: self.env.user, tracking=True)
    observaciones = fields.Text(string='Observaciones generales')
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('cerrado', 'Cerrado'),
    ], default='borrador', string='Estado', tracking=True)
    linea_ids = fields.One2many(
        'amunet.reg.entrega.vest.linea', 'registro_id', string='Registros')

    firma_id = fields.Many2one('res.users', string='Firmó', readonly=True)
    fecha_firma = fields.Datetime(string='Fecha de firma', readonly=True)

    total_personas = fields.Integer(compute='_compute_total', store=True)

    @api.depends('linea_ids')
    def _compute_total(self):
        for rec in self:
            rec.total_personas = len(rec.linea_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'amunet.reg.entrega.vest') or 'Nuevo'
        return super().create(vals_list)

    def action_cerrar(self):
        for rec in self:
            if not rec.linea_ids:
                raise UserError('Agrega al menos un registro antes de cerrar.')
            rec.write({'state': 'cerrado'})

    def action_reabrir(self):
        self.write({'state': 'borrador'})

    def _amunet_signature_allowed_methods(self):
        return {'action_firmar_responsable': 'Firma del responsable'}

    def action_firmar_responsable(self):
        self.write({
            'firma_id': self.env.user.id,
            'fecha_firma': fields.Datetime.now(),
        })


class AmunetRegEntregaVestLinea(models.Model):
    _name = 'amunet.reg.entrega.vest.linea'
    _description = 'Línea — Entrega de Indumentaria'
    _order = 'sequence, id'

    registro_id = fields.Many2one(
        'amunet.reg.entrega.vest', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    empleado_nombre = fields.Char(string='Nombre', required=True)

    bata_color = fields.Char(string='Color')
    bata_talla = fields.Selection([
        ('XS', 'XS'), ('S', 'S'), ('M', 'M'),
        ('L', 'L'), ('XL', 'XL'), ('XXL', 'XXL'),
    ], string='Talla')
    bata_cantidad = fields.Integer(string='Prendas', default=1)
    bata_fecha = fields.Date(string='Fecha')

    zapatos_color = fields.Char(string='Color')
    zapatos_talla = fields.Char(string='Talla')
    zapatos_cantidad = fields.Integer(string='Prendas', default=1)
    zapatos_fecha = fields.Date(string='Fecha')

    notas = fields.Char(string='Notas')
