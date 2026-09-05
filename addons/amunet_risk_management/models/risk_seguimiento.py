from odoo import api, fields, models
from odoo.exceptions import UserError


class AmunetRiskSeguimiento(models.Model):
    _name = 'amunet.risk.seguimiento'
    _description = 'Seguimiento de Acciones de Riesgo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha desc, id desc'

    name = fields.Char(string='Folio', readonly=True, copy=False, default='Nuevo')
    analisis_id = fields.Many2one(
        'amunet.risk.analysis', string='Análisis AMEF', required=True, tracking=True)
    linea_id = fields.Many2one(
        'amunet.risk.analysis.linea', string='Modo de falla',
        domain="[('analisis_id', '=', analisis_id)]", tracking=True)
    fecha = fields.Date(
        string='Fecha de verificación', default=fields.Date.today, required=True, tracking=True)
    verifico_id = fields.Many2one(
        'res.users', string='Verificó',
        default=lambda self: self.env.user, required=True, tracking=True)

    actividad = fields.Char(
        string='Actividad de seguimiento', required=True,
        help='Describe qué se verificó o qué acción se revisó.')
    resultado = fields.Text(string='Resultado / Observaciones')
    eficacia = fields.Selection([
        ('eficaz', 'Eficaz'),
        ('parcial', 'Parcialmente eficaz'),
        ('no_eficaz', 'No eficaz'),
    ], string='Eficacia de la acción', tracking=True)

    state = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En proceso'),
        ('completado', 'Completado'),
    ], string='Estado', default='pendiente', tracking=True)

    firma_id = fields.Many2one('res.users', string='Cerró', readonly=True)
    fecha_firma = fields.Datetime(string='Fecha de cierre', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'amunet.risk.seguimiento') or 'Nuevo'
        return super().create(vals_list)

    def action_cerrar(self):
        self.ensure_one()
        if not self.eficacia:
            raise UserError('Indica la eficacia de la acción antes de cerrar.')
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_cerrar', 'Cierre de seguimiento de riesgo')

    def _signature_cerrar(self):
        self.ensure_one()
        self.write({
            'state': 'completado',
            'firma_id': self.env.user.id,
            'fecha_firma': fields.Datetime.now(),
        })

    def _amunet_signature_allowed_methods(self):
        return {'_signature_cerrar': 'Cierre de seguimiento de riesgo'}
