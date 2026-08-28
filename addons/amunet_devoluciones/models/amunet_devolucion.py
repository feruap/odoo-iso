# -*- coding: utf-8 -*-
from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError

ESTADOS = [
    ('pending_reception', 'Esperando recepcion'),
    ('received', 'Recibido, en cuarentena'),
    ('released', 'Liberado por calidad'),
    ('rejected', 'Rechazado por calidad'),
]


class AmunetDevolucion(models.Model):
    """Material que regresa de un pedido cancelado.

    El registro nace en la tienda -ahi se cancela el pedido y ahi se contesta si
    hay devolucion- y aqui se le da seguimiento: quien lo recibio, cuanto llego
    de verdad, que dijo calidad y a que anaquel volvio.

    Los dos sistemas guardan el mismo expediente. La tienda es la que sabe que
    pedido era; Odoo es el que sabe donde esta el material.
    """
    _name = 'amunet.devolucion'
    _description = 'Devolucion de material por cancelacion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_apertura desc, id desc'
    _rec_name = 'referencia'

    referencia = fields.Char(string='Referencia', required=True, index=True, copy=False,
                             help='El identificador de la devolucion en la tienda.')
    woo_return_id = fields.Integer(string='Id en la tienda', required=True, index=True, copy=False)
    woo_order_id = fields.Integer(string='Pedido', index=True, readonly=True)
    woo_sku = fields.Char(string='Clave', readonly=True)
    woo_producto = fields.Char(string='Producto en la tienda', readonly=True)

    product_id = fields.Many2one('product.product', string='Producto', readonly=True,
                                 help='El producto de Odoo al que corresponde la clave de la tienda.')
    lot_id = fields.Many2one('stock.lot', string='Lote', domain="[('product_id','=',product_id)]",
                             tracking=True,
                             help='De que lote salio. Sin lote no se puede saber su caducidad, '
                                  'y por lo tanto tampoco a que anaquel debe volver.')

    cantidad_declarada = fields.Float(string='Piezas declaradas', readonly=True,
                                      digits='Product Unit of Measure')
    cantidad_recibida = fields.Float(string='Piezas recibidas', tracking=True,
                                     digits='Product Unit of Measure',
                                     help='Lo que el almacen tiene enfrente. Puede llegar menos '
                                          'de lo que se declaro.')
    cantidad_liberada = fields.Float(string='Piezas liberadas', readonly=True, tracking=True,
                                     digits='Product Unit of Measure')
    cantidad_desechada = fields.Float(string='Piezas desechadas', readonly=True, tracking=True,
                                      digits='Product Unit of Measure')

    motivo = fields.Char(string='Motivo de la cancelacion', readonly=True)
    estado = fields.Selection(ESTADOS, string='Estado', default='pending_reception',
                              required=True, index=True, tracking=True)

    fecha_apertura = fields.Datetime(string='Abierta el', readonly=True)
    recibido_por_id = fields.Many2one('res.users', string='Recibido por', readonly=True)
    fecha_recepcion = fields.Datetime(string='Recibido el', readonly=True)
    evaluado_por_id = fields.Many2one('res.users', string='Firmado por', readonly=True,
                                      help='Quien de calidad firmo el dictamen con su PIN.')
    fecha_evaluacion = fields.Datetime(string='Evaluado el', readonly=True)
    dictamen = fields.Text(string='Dictamen de calidad', tracking=True)

    picking_recepcion_id = fields.Many2one('stock.picking', string='Traslado de entrada',
                                           readonly=True, copy=False)
    picking_salida_id = fields.Many2one('stock.picking', string='Traslado de salida',
                                        readonly=True, copy=False)

    condicion_al_volver = fields.Selection(
        related='lot_id.amunet_condicion_caducidad', string='Condicion del lote hoy', readonly=True)

    # Odoo 19 ya no acepta _sql_constraints; la restriccion se declara asi.
    _woo_return_id_unico = models.Constraint(
        'unique(woo_return_id)',
        'Esa devolucion de la tienda ya esta registrada.',
    )

    # ------------------------------------------------------------------
    def _ubicacion_cuarentena(self):
        ubicacion = self.env.ref('amunet_devoluciones.location_devoluciones',
                                 raise_if_not_found=False)
        if not ubicacion:
            raise UserError(_(
                'Falta el anaquel de cuarentena "APT/Devoluciones por evaluar". '
                'Pide a sistemas que lo cree antes de recibir devoluciones.'))
        return ubicacion

    def _tipo_traslado(self):
        almacen = self.env['stock.warehouse'].search([('code', '=', 'APT')], limit=1)
        if almacen and almacen.int_type_id:
            return almacen.int_type_id
        tipo = self.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1)
        if not tipo:
            raise UserError(_('No hay un tipo de operacion de traslado interno configurado.'))
        return tipo

    def _mover(self, origen, destino, cantidad, motivo):
        """Un traslado interno validado. Nada de ajustes silenciosos."""
        self.ensure_one()
        if cantidad <= 0:
            return self.env['stock.picking']
        if not self.lot_id:
            raise UserError(_('Falta decir de que lote es esta devolucion.'))
        picking = self.env['stock.picking'].create({
            'picking_type_id': self._tipo_traslado().id,
            'location_id': origen.id,
            'location_dest_id': destino.id,
            'origin': motivo,
        })
        movimiento = self.env['stock.move'].create({
            'picking_id': picking.id,
            'product_id': self.product_id.id,
            'product_uom_qty': cantidad,
            'product_uom': self.product_id.uom_id.id,
            'location_id': origen.id,
            'location_dest_id': destino.id,
        })
        picking.action_confirm()
        movimiento.move_line_ids = [Command.clear(), Command.create({
            'product_id': self.product_id.id,
            'product_uom_id': self.product_id.uom_id.id,
            'lot_id': self.lot_id.id,
            'quantity': cantidad,
            'location_id': origen.id,
            'location_dest_id': destino.id,
            'picking_id': picking.id,
            'picked': True,
        })]
        movimiento.picked = True
        if not picking.amunet_validar():
            raise UserError(_(
                'El traslado %s no se pudo validar. Revisalo antes de continuar: '
                'el material no se movio.') % picking.name)
        return picking

    # ------------------------------------------------------------------
    def action_recibir(self):
        """Almacen confirma que llego, y cuanto."""
        for dev in self:
            if dev.estado != 'pending_reception':
                raise UserError(_('Esta devolucion ya se habia recibido.'))
            if not dev.lot_id:
                raise UserError(_(
                    'Antes de recibir hay que decir de que lote es. Sin el lote no se '
                    'sabe su caducidad, y sin caducidad no se sabe a que anaquel volveria.'))
            if dev.cantidad_recibida <= 0:
                raise UserError(_('Captura cuantas piezas recibiste.'))

            # Entra al inventario en cuarentena. Viene de fuera: el origen es la
            # ubicacion de clientes, igual que una devolucion de venta normal.
            clientes = dev.env.ref('stock.stock_location_customers', raise_if_not_found=False)
            if not clientes:
                clientes = dev.env['stock.location'].search([('usage', '=', 'customer')], limit=1)
            if not clientes:
                raise UserError(_('No hay una ubicacion de clientes configurada.'))
            picking = dev._mover(clientes, dev._ubicacion_cuarentena(), dev.cantidad_recibida,
                                 _('Devolucion %s') % dev.referencia)
            dev.write({
                'estado': 'received',
                'recibido_por_id': dev.env.user.id,
                'fecha_recepcion': fields.Datetime.now(),
                'picking_recepcion_id': picking.id,
            })
            dev.message_post(body=_(
                'Recibidas %(cant)s piezas del lote %(lote)s. Quedan en cuarentena hasta que '
                'calidad las revise.',
                cant=dev.cantidad_recibida, lote=dev.lot_id.name))
            dev._avisar_a_la_tienda('received')
        return True

    def action_dictaminar(self):
        """Abre la firma de calidad. Nadie libera sin identificarse."""
        self.ensure_one()
        self._exigir_recibido()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Dictamen de calidad'),
            'res_model': 'amunet.devolucion.firma',
            'view_mode': 'form',
            'target': 'new',
            'context': dict(self.env.context, active_id=self.id),
        }

    def _liberar(self, liberar, dictamen):
        """Calidad libera. Vuelve al anaquel que le toca HOY.

        Se llama desde la firma, nunca desde un boton directo: la decision de
        poner un producto sanitario devuelto otra vez a la venta tiene que estar
        atada a la persona que la tomo.
        """
        for dev in self:
            dev._exigir_recibido()
            liberar = float(liberar or 0)
            if liberar <= 0 or liberar > dev.cantidad_recibida:
                raise UserError(_(
                    'Las piezas liberadas tienen que estar entre 1 y %s.') % dev.cantidad_recibida)
            dev.dictamen = dictamen
            desechar = dev.cantidad_recibida - liberar

            # Aqui esta el punto: el lote conserva su fecha, pero paso tiempo.
            # Si mientras estaba fuera entro a caducidad corta, no vuelve al
            # anaquel normal.
            destino = dev.lot_id._amunet_destino_esperado()
            if not destino:
                almacen = dev.env['stock.warehouse'].search([('code', '=', 'APT')], limit=1)
                destino = almacen.lot_stock_id
            picking = dev._mover(dev._ubicacion_cuarentena(), destino, liberar,
                                 _('Liberacion de la devolucion %s') % dev.referencia)

            if desechar > 0:
                retenidos = dev.env.ref('amunet_caducidad_alerta.location_retenidos',
                                        raise_if_not_found=False)
                if retenidos:
                    dev._mover(dev._ubicacion_cuarentena(), retenidos, desechar,
                               _('Rechazo parcial de la devolucion %s') % dev.referencia)

            dev.write({
                'estado': 'released',
                'cantidad_liberada': liberar,
                'cantidad_desechada': desechar,
                'evaluado_por_id': dev.env.user.id,
                'fecha_evaluacion': fields.Datetime.now(),
                'picking_salida_id': picking.id,
            })
            dev.message_post(body=_(
                'Calidad libero %(lib)s piezas y desecho %(des)s. Regresaron a %(dest)s. '
                'Firmado con PIN por %(quien)s.',
                lib=liberar, des=desechar, dest=destino.display_name,
                quien=dev.env.user.name))
            dev._avisar_a_la_tienda('released')
        return True

    def _rechazar(self, dictamen):
        """Calidad rechaza todo. Se va a retenidos, no a la basura sin registro."""
        for dev in self:
            dev._exigir_recibido()
            dev.dictamen = dictamen
            retenidos = dev.env.ref('amunet_caducidad_alerta.location_retenidos',
                                    raise_if_not_found=False)
            if not retenidos:
                raise UserError(_('Falta el anaquel de retenidos.'))
            picking = dev._mover(dev._ubicacion_cuarentena(), retenidos, dev.cantidad_recibida,
                                 _('Rechazo de la devolucion %s') % dev.referencia)
            dev.write({
                'estado': 'rejected',
                'cantidad_liberada': 0,
                'cantidad_desechada': dev.cantidad_recibida,
                'evaluado_por_id': dev.env.user.id,
                'fecha_evaluacion': fields.Datetime.now(),
                'picking_salida_id': picking.id,
            })
            dev.message_post(body=_(
                'Calidad rechazo la devolucion completa. Firmado con PIN por %(quien)s. %(dic)s',
                quien=dev.env.user.name, dic=dev.dictamen or ''))
            dev._avisar_a_la_tienda('rejected')
        return True

    def _exigir_recibido(self):
        self.ensure_one()
        if self.estado != 'received':
            raise UserError(_('Calidad solo puede dictaminar lo que el almacen ya recibio.'))

    # ------------------------------------------------------------------
    def _avisar_a_la_tienda(self, estado):
        """Le devuelve el estado a la tienda, para que los dos expedientes coincidan."""
        self.ensure_one()
        backend = self.env['amunet.woo.backend'].search([('active', '=', True)], limit=1)
        if not backend or not backend.bridge_secret:
            self.message_post(body=_(
                'No se pudo avisar a la tienda: el puente no esta configurado. '
                'El estado en la tienda hay que ponerlo a mano.'))
            return False
        try:
            backend._call_bridge('POST', 'devoluciones/%s/estado' % self.woo_return_id, {
                'estado': estado,
                'cantidad_recibida': self.cantidad_recibida,
                'cantidad_liberada': self.cantidad_liberada,
                'cantidad_desechada': self.cantidad_desechada,
                'dictamen': self.dictamen or '',
                # Al liberar, la tienda tiene que volver a contar estas piezas.
                # El lote y su caducidad viajan para que entren con su fecha
                # real, no con una nueva: la caducidad no se renueva porque el
                # producto haya ido y vuelto.
                'lote': self.lot_id.name or '',
                'caducidad': self.lot_id.expiration_date and
                             fields.Datetime.to_string(self.lot_id.expiration_date) or '',
            })
        except Exception as exc:      # noqa: BLE001 - se reporta, no se traga
            self.message_post(body=_('La tienda no acepto el aviso: %s') % exc)
            return False
        return True

    @api.model
    def _cron_traer_de_la_tienda(self):
        return self.traer_de_la_tienda()

    @api.model
    def traer_de_la_tienda(self):
        """Trae las devoluciones abiertas en la tienda que aun no estan aqui."""
        backend = self.env['amunet.woo.backend'].search([('active', '=', True)], limit=1)
        if not backend or not backend.bridge_secret:
            raise UserError(_('El puente con la tienda no esta configurado.'))
        datos = backend._call_bridge('POST', 'devoluciones/pendientes', {}) or {}
        nuevas = self.browse()
        for fila in datos.get('devoluciones', []):
            woo_id = int(fila.get('id') or 0)
            if not woo_id or self.search_count([('woo_return_id', '=', woo_id)]):
                continue
            producto = self._producto_por_clave(fila.get('sku'))
            nuevas |= self.create({
                'referencia': 'DEV/%s' % woo_id,
                'woo_return_id': woo_id,
                'woo_order_id': int(fila.get('order_id') or 0),
                'woo_sku': fila.get('sku') or '',
                'woo_producto': fila.get('producto') or '',
                'product_id': producto.id if producto else False,
                'cantidad_declarada': float(fila.get('cantidad') or 0),
                'cantidad_recibida': float(fila.get('cantidad') or 0),
                'motivo': fila.get('motivo') or '',
                'fecha_apertura': fila.get('fecha') or fields.Datetime.now(),
                'estado': 'pending_reception',
            })
        return nuevas

    @api.model
    def _producto_por_clave(self, sku):
        """La clave de la tienda apunta a la caja; el lote es de la pieza."""
        if not sku:
            return self.env['product.product']
        Mapeo = self.env.get('amunet.woo.product.mapping')
        if Mapeo is not None:
            mapeo = Mapeo.search([('woo_sku', '=', sku)], limit=1)
            if mapeo and mapeo.product_id:
                return mapeo.product_id
        clave = (sku or '').split('.')[0].split('-')[0]
        return self.env['product.product'].search([('default_code', '=', clave)], limit=1)
