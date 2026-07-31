from odoo import models, fields, api, _
from odoo.exceptions import UserError

DIANA_UID = 64
JORGE_UID = 70

_QUALITY_GROUPS = [
    'amunet_quality.group_quality_user',
    'amunet_quality.group_quality_supervisor',
    'amunet_quality.group_quality_manager',
]


class AmunetAvisoProduccion(models.Model):
    _name = 'amunet.aviso.produccion'
    _description = 'Aviso de cambio en produccion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Referencia', readonly=True, copy=False,
                       default='Nuevo aviso')
    state = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('cerrado', 'Cerrado'),
        ('rechazado', 'Rechazado'),
    ], default='pendiente', string='Estado', tracking=True, readonly=True)

    production_id = fields.Many2one('mrp.production', string='Orden de fabricacion',
                                    tracking=True)
    product_id = fields.Many2one(related='production_id.product_id',
                                 string='Producto', store=True)

    descripcion = fields.Text(string='Que notaste diferente', required=True)
    instruccion_vigente = fields.Text(string='Que dice el proceso original')
    instruccion_propuesta = fields.Text(string='Que se hizo en cambio')

    requested_by_id = fields.Many2one('res.users', string='Enviado por',
                                      readonly=True, tracking=True)
    fecha_envio = fields.Datetime(string='Fecha de envio', readonly=True)

    evaluacion = fields.Text(string='Evaluacion de Calidad')
    firmado_por_id = fields.Many2one('res.users', string='Revisado por',
                                     readonly=True)
    fecha_cierre = fields.Datetime(string='Fecha de cierre', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo aviso') == 'Nuevo aviso':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'amunet.aviso.produccion') or 'Nuevo aviso'
        return super().create(vals_list)

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_cerrar_aviso': _('Cerrar evaluacion de aviso'),
            '_signature_rechazar_aviso': _('Rechazar aviso'),
        }

    def action_cerrar(self):
        self.ensure_one()
        if not (self.evaluacion or '').strip():
            raise UserError('Escribe tu evaluacion antes de cerrar.')
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_cerrar_aviso', 'cierre_aviso',
            reason='Cierre de evaluacion de aviso de produccion',
        )

    def action_rechazar(self):
        self.ensure_one()
        if not (self.evaluacion or '').strip():
            raise UserError('Escribe el motivo del rechazo en el campo Evaluacion.')
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_rechazar_aviso', 'rechazo_aviso',
            reason='Rechazo de aviso de produccion',
        )

    def _signature_cerrar_aviso(self):
        self.write({
            'state': 'cerrado',
            'firmado_por_id': self.env.user.id,
            'fecha_cierre': fields.Datetime.now(),
        })
        self._notificar_cierre('cerrado')

    def _signature_rechazar_aviso(self):
        self.write({
            'state': 'rechazado',
            'firmado_por_id': self.env.user.id,
            'fecha_cierre': fields.Datetime.now(),
        })
        self._notificar_cierre('rechazado')

    def _notificar_cierre(self, resultado):
        tipo = self.env.ref('mail.mail_activity_data_todo')
        etiqueta = 'cerrado con evaluacion' if resultado == 'cerrado' else 'rechazado'
        nota = (
            f'<p>El aviso <b>{self.name}</b> ha sido <b>{etiqueta}</b> '
            f'por {self.firmado_por_id.name}.</p>'
            f'<p><b>Evaluacion:</b> {self.evaluacion}</p>'
        )
        # Notificar a quien envio el aviso
        destinatarios = self.sudo().requested_by_id
        # + Jorge y Calidad
        destinatarios |= self.env['res.users'].sudo().browse(JORGE_UID)
        for xmlid in _QUALITY_GROUPS:
            grupo = self.env.ref(xmlid, raise_if_not_found=False)
            if grupo:
                destinatarios |= grupo.sudo().user_ids
        for user in destinatarios.filtered('active'):
            if user.id != self.env.user.id:
                self.activity_schedule(
                    activity_type_id=tipo.id,
                    summary=f'Aviso {self.name} {etiqueta}',
                    note=nota,
                    user_id=user.id,
                )
