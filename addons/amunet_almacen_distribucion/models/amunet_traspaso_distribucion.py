from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AmunetTraspasoDistribucion(models.Model):
    _name = 'amunet.traspaso.distribucion'
    _description = 'Solicitud de traspaso de Producto Terminado a Distribucion'
    _order = 'create_date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Folio', required=True, copy=False, readonly=True,
        default=lambda self: _('Nuevo'))
    product_id = fields.Many2one(
        'product.product', string='Producto', required=True,
        readonly=True, index=True)
    lot_id = fields.Many2one(
        'stock.lot', string='Lote', readonly=True, index=True)
    expiration_date = fields.Datetime(
        string='Caducidad', related='lot_id.expiration_date', readonly=True)
    quantity = fields.Float(
        string='Cantidad', required=True, readonly=True,
        digits='Product Unit of Measure')
    uom_id = fields.Many2one(
        'uom.uom', string='Unidad', readonly=True)
    origin_move_id = fields.Many2one(
        'stock.move', string='Movimiento de origen', readonly=True,
        help='Movimiento que ingreso el material al anaquel de PT.')
    origin = fields.Char(string='Origen', readonly=True)
    location_id = fields.Many2one(
        'stock.location', string='Ubicacion actual', readonly=True)

    state = fields.Selection([
        ('draft', 'Por autorizar'),
        ('authorized', 'Autorizada'),
        ('rejected', 'Rechazada'),
    ], string='Estado', default='draft', required=True, tracking=True, index=True)

    decision_user_id = fields.Many2one(
        'res.users', string='Decidio', readonly=True, tracking=True)
    decision_date = fields.Datetime(string='Fecha de decision', readonly=True)
    reject_reason = fields.Text(string='Motivo del rechazo', readonly=True, tracking=True)
    picking_id = fields.Many2one(
        'stock.picking', string='Traslado generado', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nuevo')) == _('Nuevo'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'amunet.traspaso.distribucion') or _('Nuevo')
        return super().create(vals_list)

    def _param_id(self, clave, por_default):
        """Lee un id de configuracion. Evita ids fijos regados en el codigo."""
        valor = self.env['ir.config_parameter'].sudo().get_param(clave)
        try:
            return int(valor) if valor else por_default
        except (TypeError, ValueError):
            return por_default

    def _crear_traslado(self, location_dest_id, motivo):
        """Crea y valida el traslado desde el anaquel de PT al destino indicado."""
        self.ensure_one()
        tipo_id = self._param_id('amunet.distribucion.picking_type_pt', 15)
        picking_type = self.env['stock.picking.type'].browse(tipo_id)
        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': self.location_id.id,
            'location_dest_id': location_dest_id,
            'origin': '%s - %s' % (self.name, motivo),
            'move_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'product_uom_qty': self.quantity,
                'product_uom': self.uom_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': location_dest_id,
            })],
        })
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.move_line_ids.unlink()
            self.env['stock.move.line'].create({
                'move_id': move.id,
                'picking_id': picking.id,
                'product_id': self.product_id.id,
                'lot_id': self.lot_id.id or False,
                'quantity': self.quantity,
                'product_uom_id': self.uom_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': location_dest_id,
            })
        picking.button_validate()
        self.picking_id = picking.id
        return picking

    def action_autorizar(self):
        destino_id = self._param_id('amunet.distribucion.location_adt', 66)
        for req in self:
            if req.state != 'draft':
                raise UserError(_('La solicitud %s ya fue resuelta.') % req.name)
            req._crear_traslado(destino_id, _('Traspaso autorizado a Distribucion'))
            req.write({
                'state': 'authorized',
                'decision_user_id': self.env.user.id,
                'decision_date': fields.Datetime.now(),
            })
            req.message_post(body=_('Traspaso autorizado a Distribucion.'))
        return True

    def action_rechazar(self):
        """Abre el asistente que exige el motivo. El rechazo nunca va sin razon."""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('La solicitud %s ya fue resuelta.') % self.name)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Rechazar traspaso'),
            'res_model': 'amunet.traspaso.distribucion.rechazo',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_traspaso_id': self.id},
        }

    def _rechazar(self, motivo):
        destino_id = self._param_id('amunet.distribucion.location_rechazo', 55)
        self.ensure_one()
        self._crear_traslado(destino_id, _('Rechazado: %s') % motivo)
        self.write({
            'state': 'rejected',
            'reject_reason': motivo,
            'decision_user_id': self.env.user.id,
            'decision_date': fields.Datetime.now(),
        })
        self.message_post(body=_('Traspaso rechazado. Motivo: %s') % motivo)
        return True

    @api.model
    def _cron_avisar_pendientes(self):
        """Avisa al responsable las solicitudes que llevan dias sin decidir."""
        Param = self.env['ir.config_parameter'].sudo()
        try:
            dias = int(Param.get_param('amunet.distribucion.dias_aviso', 3))
        except (TypeError, ValueError):
            dias = 3
        try:
            uid = int(Param.get_param('amunet.distribucion.responsable_uid', 0))
        except (TypeError, ValueError):
            uid = 0
        if not uid:
            return
        limite = fields.Datetime.subtract(fields.Datetime.now(), days=dias)
        pendientes = self.search([
            ('state', '=', 'draft'),
            ('create_date', '<', limite),
        ])
        # Una sola actividad por solicitud, aunque el cron corra a diario.
        sin_aviso = pendientes.filtered(lambda r: not r.activity_ids)
        for req in sin_aviso:
            req.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=uid,
                summary=_('Traspaso a Distribucion sin resolver'),
                note=_('%(prod)s lote %(lote)s, %(qty)s pz en el anaquel de PT '
                       'desde hace mas de %(dias)s dias.') % {
                    'prod': req.product_id.display_name,
                    'lote': req.lot_id.name or 's/lote',
                    'qty': req.quantity,
                    'dias': dias,
                })
        return len(sin_aviso)
