# -*- coding: utf-8 -*-
"""Solicitud de COMPRA del Marketplace Interno.

Pedirle material a Almacen y comprarle a una tienda son dos cosas distintas:
distinta gente, distinta autorizacion, distintos tiempos. Hasta hoy compartian
formulario -- amunet.material.request, con 19 campos de compra inyectados por
amunet_compras_general y 4 mas por este modulo -- y las dos aplicaciones,
Marketplace Interno y Solicitudes de Material, apuntaban a la MISMA lista.
Separado por decision de Mery, 19-sep-2026.

POR QUE VIVE AQUI Y NO EN amunet_compras_general
El catalogo del Marketplace no es de almacen, es de COMPRAS: 61 de sus 62
productos traen liga de tienda (47 Mercado Libre, 14 Amazon), precio de
referencia y bandera de si requieren aprobacion. Aqui ya estaba todo lo que
acompaña a una compra -- que se compra, donde, a cuanto, y que hacer si no esta
en el catalogo. Lo unico que faltaba era su propia solicitud.
amunet_compras_general aporta encima lo suyo: forma de pago, CLABE, monto y la
autorizacion por Telegram.

LO QUE ESTA SOLICITUD NO HACE, A PROPOSITO
  - No surte ni concilia: eso es de Almacen.
  - No recibe: el material comprado entra por el flujo normal de Almacen.
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AmunetSolicitudCompra(models.Model):
    _name = 'amunet.solicitud.compra'
    _description = 'Solicitud de compra'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Folio', required=True, copy=False, readonly=True,
        default=lambda self: _('Nueva'))
    state = fields.Selection(
        [('draft', 'Borrador'),
         ('submitted', 'Enviada'),
         ('pending_approval', 'Pte. autorizacion'),
         ('approved', 'Autorizada'),
         ('purchased', 'Comprada'),
         ('closed', 'Cerrada'),
         ('cancelled', 'Cancelada')],
        string='Estado', default='draft', required=True, tracking=True,
        copy=False, index=True)

    requester_id = fields.Many2one(
        'res.users', string='Solicitante', required=True, tracking=True,
        default=lambda self: self.env.user, index=True)
    department_id = fields.Many2one('hr.department', string='Area', tracking=True)
    request_date = fields.Datetime(
        string='Fecha de solicitud', default=fields.Datetime.now, required=True)
    required_date = fields.Datetime(string='Fecha requerida')
    note = fields.Text(string='Justificacion')

    # La misma clasificacion que ya usa el catalogo del marketplace, para que
    # una solicitud se pueda filtrar igual que los productos que pide.
    marketplace_flow = fields.Selection(
        selection=[('general', 'Compra general'),
                   ('production', 'Produccion / fabricacion')],
        string='Tipo de compra', default='general', required=True, tracking=True)

    line_ids = fields.One2many(
        'amunet.solicitud.compra.line', 'request_id', string='Que se compra',
        copy=True)

    partner_id = fields.Many2one(
        'res.partner', string='Proveedor', tracking=True,
        help='Solo cuando se le compra a un proveedor con alta. Si se compra '
             'en tienda, el camino es la liga de cada renglon.')
    purchase_order_id = fields.Many2one(
        'purchase.order', string='Orden de compra', readonly=True, copy=False,
        help='La orden que genero esta solicitud, si aplica.')

    # Rastro de la solicitud de material que la origino, en las migradas.
    # ------------------------------------------------------------------
    # Recepcion en almacen: al autorizar la compra se genera la orden de
    # entrada para que Almacen sepa que va a llegar y pueda recibirlo con
    # el flujo normal (cuarentena de Calidad incluida donde aplique).
    # ------------------------------------------------------------------
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Almacen por omision',
        default=lambda self: self.env['stock.warehouse'].search(
            [('code', '=', 'AMP')], limit=1),
        tracking=True,
        help='Se usa para los renglones que no traen almacen propio. Cada '
             'renglon puede llegar a un almacen distinto.')
    picking_ids = fields.One2many(
        'stock.picking', 'amunet_solicitud_compra_id',
        string='Ordenes de recepcion', readonly=True,
        help='Se generan solas al autorizar: una por almacen que recibe.')
    picking_count = fields.Integer(compute='_compute_picking_count')

    @api.depends('picking_ids')
    def _compute_picking_count(self):
        for req in self:
            req.picking_count = len(req.picking_ids)

    amunet_material_request_id = fields.Many2one(
        'amunet.material.request', string='Solicitud de material de origen',
        readonly=True, copy=False,
        help='Solo en las que se migraron del flujo anterior, cuando compras y '
             'material compartian formulario.')

    requiere_aprobacion = fields.Boolean(
        string='Requiere aprobacion', compute='_compute_requiere_aprobacion',
        store=True,
        help='Se enciende solo si alguno de los productos pedidos la exige, '
             'segun su ficha en el catalogo interno.')

    @api.depends('line_ids.product_id')
    def _compute_requiere_aprobacion(self):
        for req in self:
            req.requiere_aprobacion = any(
                l.product_id.product_tmpl_id.marketplace_requires_approval
                for l in req.line_ids if l.product_id)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nueva')) == _('Nueva'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'amunet.solicitud.compra') or _('Nueva')
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Flujo: enviar -> autorizar (jefe del area) -> comprada -> cerrada
    #
    # Esta es la PRIMERA firma, la del jefe directo de quien pide. La segunda
    # -- el visto bueno de Fernando por Telegram antes de pagar -- vive en
    # amunet_compras_general junto con el monto, y se engancha aqui cuando ese
    # modulo apunte a este modelo.
    # ------------------------------------------------------------------
    amunet_aprobador_id = fields.Many2one(
        'res.users', string='Debe autorizar', compute='_compute_aprobador',
        help='El jefe directo de quien pide, tomado de Recursos Humanos.')
    amunet_usuario_es_aprobador = fields.Boolean(
        compute='_compute_aprobador',
        help='Tecnico: si el usuario de la sesion es quien debe autorizar.')
    amunet_autorizada_por_id = fields.Many2one(
        'res.users', string='Autorizada por', readonly=True, copy=False)
    amunet_autorizada_fecha = fields.Datetime(
        string='Fecha de autorizacion', readonly=True, copy=False)

    @api.depends_context('uid')
    @api.depends('requester_id')
    def _compute_aprobador(self):
        for req in self:
            jefe = req.sudo().requester_id.amunet_material_head_id
            req.amunet_aprobador_id = jefe.id if jefe else False
            req.amunet_usuario_es_aprobador = bool(jefe and jefe.id == self.env.uid)

    def action_enviar(self):
        for req in self:
            if req.state != 'draft':
                raise ValidationError(_('Solo se envia una solicitud en borrador.'))
            if not req.line_ids:
                raise ValidationError(_(
                    'Agrega al menos un renglon antes de enviar la solicitud.'))
            req.state = 'pending_approval'
            jefe = req.amunet_aprobador_id
            if jefe:
                req.message_post(body=_(
                    'Enviada. Espera la autorizacion de %s.') % jefe.name)
                req.activity_schedule(
                    'mail.mail_activity_data_todo', user_id=jefe.id,
                    summary=_('Autorizar solicitud de compra %s') % req.name)
            else:
                req.message_post(body=_(
                    'Enviada. <b>Quien la pide no tiene jefe asignado en '
                    'Recursos Humanos</b>, asi que nadie puede autorizarla '
                    'todavia: hay que asignarle responsable o autorizarla '
                    'desde el area de compras.'))
        return True

    def action_autorizar(self):
        """Solo el jefe directo, o compras. Nadie autoriza lo que pidio."""
        for req in self:
            if req.state != 'pending_approval':
                raise ValidationError(_(
                    'Solo se autoriza una solicitud que este esperando '
                    'autorizacion.'))
            es_compras = self.env.user.has_group(
                'amunet_material_request.group_material_manager')
            if not (req.amunet_usuario_es_aprobador or es_compras or self.env.su):
                quien = req.amunet_aprobador_id.name or _('el jefe del area')
                raise ValidationError(_(
                    'Esta solicitud la autoriza %s. Segregacion de funciones: '
                    'quien pide no aprueba su propia compra.') % quien)
            if req.requester_id.id == self.env.uid and not self.env.su:
                raise ValidationError(_(
                    'No puedes autorizar una solicitud que tu misma pediste.'))
            req._check_destino_definido()
            req.write({
                'state': 'approved',
                'amunet_autorizada_por_id': self.env.uid,
                'amunet_autorizada_fecha': fields.Datetime.now(),
            })
            req.message_post(body=_('Autorizada por %s.') % self.env.user.name)
            req.activity_unlink(['mail.mail_activity_data_todo'])
            req._generar_recepcion()
        return True

    def _check_destino_definido(self):
        """Nadie autoriza una compra sin saber a que almacen llega.

        Un producto marcado 'Ambos' vive en materia prima y en distribucion:
        el sistema no puede adivinar para que se esta pidiendo.
        """
        self.ensure_one()
        sin_destino = self.line_ids.filtered(
            lambda l: l.product_id and not l.warehouse_id)
        if sin_destino:
            detalle = '\n'.join(
                '  - %s' % l.product_id.display_name for l in sin_destino)
            raise ValidationError(_(
                'Falta decir a que almacen llega:\n\n%s\n\n'
                'Estos productos viven en Materia Prima y en Distribucion. '
                'Indica el almacen en cada renglon antes de autorizar.'
            ) % detalle)

    def _generar_recepcion(self):
        """Crea las ordenes de entrada, una por almacen que recibe.

        Una misma solicitud puede pedir puntas para distribucion y un reactivo
        para materia prima: cada almacen recibe la suya.

        Solo mueve renglones con producto dado de alta: un renglon escrito a
        mano (todavia sin clave) no puede generar movimiento de inventario.
        """
        self.ensure_one()
        if self.picking_ids:
            return self.picking_ids
        lineas = self.line_ids.filtered('product_id')
        if not lineas:
            self.message_post(body=_(
                'No se genero orden de recepcion: ningun renglon tiene un '
                'producto dado de alta en el sistema. Cuando se codifique el '
                'producto, crea la entrada a mano.'))
            return False

        por_almacen = {}
        for linea in lineas:
            almacen = linea.warehouse_id or self.warehouse_id
            if almacen:
                por_almacen.setdefault(almacen, self.env[
                    'amunet.solicitud.compra.line'])
                por_almacen[almacen] |= linea

        proveedores = self.env.ref('stock.stock_location_suppliers')
        creadas = self.env['stock.picking']
        for almacen, grupo in por_almacen.items():
            tipo = almacen.in_type_id
            if not tipo:
                self.message_post(body=_(
                    'El almacen %s no tiene configurado tipo de recepcion, '
                    'asi que no se genero su orden de entrada.') % almacen.name)
                continue
            origen = tipo.default_location_src_id or proveedores
            destino = tipo.default_location_dest_id or almacen.lot_stock_id
            picking = self.env['stock.picking'].sudo().create({
                'picking_type_id': tipo.id,
                'location_id': origen.id,
                'location_dest_id': destino.id,
                'partner_id': self.partner_id.id or False,
                'origin': self.name,
                'scheduled_date': self.required_date or fields.Datetime.now(),
                'amunet_solicitud_compra_id': self.id,
                'move_ids': [(0, 0, {
                    'description_picking': l.name or l.product_id.display_name,
                    'product_id': l.product_id.id,
                    'product_uom_qty': l.qty or 1.0,
                    'product_uom': (l.uom_id or l.product_id.uom_id).id,
                    'location_id': origen.id,
                    'location_dest_id': destino.id,
                }) for l in grupo],
            })
            picking.action_confirm()
            creadas |= picking

        omitidas = len(self.line_ids) - len(lineas)
        if creadas:
            detalle = ''.join(
                '<li><b>%s</b> en %s</li>' % (
                    p.name, p.picking_type_id.warehouse_id.name)
                for p in creadas)
            aviso = _(
                'Autorizada. Se generaron las ordenes de recepcion:<ul>%s</ul>'
                'Cada almacen ya sabe que va a llegar este material.'
            ) % detalle
            if omitidas:
                aviso += _(
                    ' <b>Quedaron fuera %s renglon(es)</b> por no tener '
                    'producto dado de alta.') % omitidas
            self.message_post(body=aviso)
        return creadas

    def action_ver_recepcion(self):
        self.ensure_one()
        if not self.picking_ids:
            raise ValidationError(_('Esta solicitud no tiene orden de recepcion.'))
        accion = {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'name': _('Recepciones de %s') % self.name,
            'domain': [('id', 'in', self.picking_ids.ids)],
            'view_mode': 'list,form',
            'target': 'current',
        }
        if len(self.picking_ids) == 1:
            accion.update(view_mode='form', res_id=self.picking_ids.id,
                          domain=[])
        return accion

    def action_marcar_comprada(self):
        for req in self:
            if req.state != 'approved':
                raise ValidationError(_(
                    'Primero hay que autorizar la solicitud.'))
            req.state = 'purchased'
            req.message_post(body=_('Marcada como comprada por %s.')
                             % self.env.user.name)
        return True

    def action_cerrar(self):
        for req in self:
            if req.state not in ('purchased', 'approved'):
                raise ValidationError(_(
                    'Solo se cierra una solicitud ya comprada.'))
            abiertas = req.picking_ids.filtered(
                lambda p: p.state not in ('done', 'cancel'))
            if abiertas:
                raise ValidationError(_(
                    'Almacen todavia no valida la recepcion %s. Se cierra '
                    'cuando el material ya entro al inventario.')
                    % ', '.join(abiertas.mapped('name')))
            req.state = 'closed'
            req.message_post(body=_('Cerrada: el material llego y se recibio '
                                    'en Almacen.'))
        return True

    def action_cancelar(self):
        for req in self:
            if req.state == 'closed':
                raise ValidationError(_('Una solicitud cerrada ya no se cancela.'))
            req.state = 'cancelled'
            req.activity_unlink(['mail.mail_activity_data_todo'])
            req.message_post(body=_('Cancelada por %s.') % self.env.user.name)
        return True

    def action_volver_borrador(self):
        for req in self:
            if req.state not in ('cancelled', 'pending_approval'):
                raise ValidationError(_(
                    'Solo vuelve a borrador una solicitud cancelada o que aun '
                    'espera autorizacion.'))
            req.write({'state': 'draft', 'amunet_autorizada_por_id': False,
                       'amunet_autorizada_fecha': False})
        return True

    @api.constrains('line_ids')
    def _check_tiene_lineas(self):
        for req in self:
            if req.state != 'draft' and not req.line_ids:
                raise ValidationError(_(
                    'La solicitud %s no tiene nada que comprar. Agrega al menos '
                    'un renglon antes de enviarla.') % req.name)


class AmunetSolicitudCompraLine(models.Model):
    _name = 'amunet.solicitud.compra.line'
    _description = 'Linea de solicitud de compra'

    request_id = fields.Many2one(
        'amunet.solicitud.compra', string='Solicitud', required=True,
        ondelete='cascade', index=True)
    product_id = fields.Many2one(
        'product.product', string='Producto del catalogo',
        domain="[('product_tmpl_id.marketplace_enabled','=',True)]",
        help='Del catalogo interno. Si lo que necesitas no esta, dejalo vacio '
             'y describelo, o levanta una propuesta de producto.')
    proposal_id = fields.Many2one(
        'amunet.marketplace.product.proposal', string='Propuesta',
        help='Cuando lo pedido todavia no existe en el catalogo.')
    name = fields.Char(string='Descripcion', required=True)
    qty = fields.Float(string='Cantidad', default=1.0, required=True)
    uom_id = fields.Many2one('uom.uom', string='Unidad')
    purchase_url = fields.Char(
        string='Liga de compra',
        help='De donde se compra. Se trae del catalogo y se puede corregir: '
             'un enlace caduca o cambia de precio.')
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Almacen que recibe',
        compute='_compute_warehouse_id', store=True, readonly=False,
        help='Lo propone el producto. Si el producto vive en los dos '
             'almacenes hay que elegirlo a mano.')
    @api.depends('product_id')
    def _compute_warehouse_id(self):
        Alm = self.env['stock.warehouse']
        amp = Alm.search([('code', '=', 'AMP')], limit=1)
        adt = Alm.search([('code', '=', 'ADT')], limit=1)
        for linea in self:
            destino = linea.product_id.product_tmpl_id.amunet_destino_almacen
            if destino == 'adt':
                linea.warehouse_id = adt
            elif destino == 'mp':
                linea.warehouse_id = amp
            else:
                # 'ambos' o sin producto: lo decide quien pide
                linea.warehouse_id = False

    note = fields.Char(string='Notas')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Trae del catalogo lo que ya esta capturado ahi, para no recapturarlo."""
        if not self.product_id:
            return
        tmpl = self.product_id.product_tmpl_id
        self.name = self.product_id.display_name
        self.uom_id = self.product_id.uom_id
        self.purchase_url = tmpl.marketplace_purchase_url or False
        if tmpl.marketplace_request_note and not self.note:
            self.note = tmpl.marketplace_request_note

    @api.constrains('product_id', 'proposal_id', 'name')
    def _check_algo_que_comprar(self):
        for l in self:
            if not (l.product_id or l.proposal_id or (l.name or '').strip()):
                raise ValidationError(_(
                    'Cada renglon necesita un producto del catalogo, una '
                    'propuesta, o al menos una descripcion de lo que se pide.'))
