# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AmunetWooDelivery(models.Model):
    """Entrega de material de Acondicionado al almacén de venta (woolibre).

    Es el primero de los DOS pasos con los que el material llega al almacén que
    surte a la tienda, y reproduce en Odoo lo que antes hacía el plugin
    AlmacenPT ("alguien entrega y el almacén acepta"):

        1) ACONDICIONADO registra la ENTREGA desde la orden de fabricación,
           declarando si es COMPLETA o PARCIAL y con cuántas piezas (aquí).
        2) El ALMACÉN de venta cuenta lo que realmente recibió y lo confirma
           (crea una ``amunet.woo.reception``).

    Control de dos partes (ISO 13485): quien entrega declara y quien recibe
    confirma. Si las cantidades NO coinciden, la entrega se RECHAZA COMPLETA
    para aclararla; no se acepta a medias, porque una diferencia sin resolver
    es justo lo que después aparece como existencia fantasma en la tienda.

    Liberación de Calidad y concesión (ISO 13485 8.3)
    -------------------------------------------------
    La realidad operativa es que a veces el material urge y se entrega ANTES de
    que Calidad libere el lote. Por eso la entrega NO se bloquea; se marca
    ``sin_liberacion`` de forma bien visible y entonces:

    - sin liberación y SIN autorización -> el material entra RETENIDO: se puede
      recibir físicamente, pero NO es vendible ni se publica a la tienda;
    - sin liberación y CON autorización (solo Mery/PM o Calidad, grupo
      ``group_woo_autoriza_concesion``) -> es vendible bajo CONCESIÓN, y queda
      registrado con nombre y fecha de quien la autorizó.

    Así la responsabilidad queda documentada donde corresponde y el almacén no
    carga con material que le entregaron sin liberar.
    """

    _name = 'amunet.woo.delivery'
    _description = 'Entrega de material a almacén de venta'
    _inherit = ['mail.thread']
    _order = 'id desc'
    _rec_name = 'display_label'

    # ------------------------------------------------------------------
    # Origen: la orden de fabricación (su nombre ES el lote)
    # ------------------------------------------------------------------

    production_id = fields.Many2one(
        'mrp.production', string='Orden de fabricación', required=True,
        ondelete='restrict', index=True, tracking=True,
        help='La entrega siempre sale de una orden de fabricación: de ahí se '
             'resuelven el producto, el lote y la caducidad, sin recapturar.')
    company_id = fields.Many2one(
        'res.company', string='Compañía', required=True,
        default=lambda self: self.env.company, index=True)
    product_id = fields.Many2one(
        'product.product', string='Producto', ondelete='restrict', index=True,
        tracking=True)
    lot_id = fields.Many2one(
        'stock.lot', string='Lote', ondelete='restrict', index=True,
        tracking=True)
    lot_number = fields.Char(string='Número de lote', tracking=True)
    expiration_month = fields.Integer(string='Mes de caducidad')
    expiration_year = fields.Integer(string='Año de caducidad')

    display_label = fields.Char(compute='_compute_display_label')

    # ------------------------------------------------------------------
    # Lo que declara Acondicionado
    # ------------------------------------------------------------------

    tipo = fields.Selection([
        ('completa', 'Entrega completa'),
        ('parcial', 'Entrega parcial'),
    ], string='Tipo de entrega', required=True, default='completa',
        tracking=True,
        help='COMPLETA entrega todo lo que queda pendiente del lote; PARCIAL '
             'entrega solo la cantidad que se capture.')
    quantity_delivered = fields.Float(
        string='Piezas entregadas', required=True, tracking=True,
        help='Lo que Acondicionado declara que está entregando.')
    delivered_by = fields.Many2one(
        'res.users', string='Entregado por', readonly=True, index=True,
        default=lambda self: self.env.user, tracking=True)
    delivered_date = fields.Datetime(
        string='Fecha de entrega', readonly=True, required=True,
        default=fields.Datetime.now, tracking=True)
    notes = fields.Text(string='Notas de la entrega')

    # ------------------------------------------------------------------
    # Lo que confirma el almacén
    # ------------------------------------------------------------------

    quantity_received = fields.Float(
        string='Piezas contadas por almacén', tracking=True,
        help='Lo que el almacén contó físicamente. Si no coincide con lo '
             'entregado, la entrega se rechaza completa para aclararla.')
    received_by = fields.Many2one(
        'res.users', string='Recibido por', readonly=True, index=True,
        tracking=True)
    received_date = fields.Datetime(
        string='Fecha de recepción', readonly=True, tracking=True)
    reception_id = fields.Many2one(
        'amunet.woo.reception', string='Recepción generada',
        ondelete='set null', readonly=True)
    rejection_reason = fields.Text(string='Motivo del rechazo', tracking=True)

    state = fields.Selection([
        ('por_recibir', 'Por recibir'),
        ('recibida', 'Recibida'),
        ('rechazada', 'Rechazada'),
        ('cancelada', 'Cancelada'),
    ], string='Estado', default='por_recibir', required=True, index=True,
        tracking=True)

    # ------------------------------------------------------------------
    # Liberación de Calidad / concesión
    # ------------------------------------------------------------------

    sin_liberacion = fields.Boolean(
        string='SIN liberación de Calidad', compute='_compute_sin_liberacion',
        store=True, readonly=True,
        help='El lote no está liberado por Calidad. La entrega se permite, '
             'pero el material NO es vendible mientras no se libere o se '
             'autorice expresamente (concesión).')
    authorized_by = fields.Many2one(
        'res.users', string='Autorizado por', readonly=True, index=True,
        tracking=True,
        help='Quien autorizó vender este material sin la liberación de '
             'Calidad (liberación bajo concesión, ISO 13485 8.3).')
    authorized_date = fields.Datetime(
        string='Fecha de autorización', readonly=True, tracking=True)
    authorization_note = fields.Text(
        string='Motivo de la autorización', tracking=True)
    vendible = fields.Boolean(
        string='Vendible', compute='_compute_vendible', store=True,
        help='Vendible si el lote está liberado por Calidad, o si se autorizó '
             'expresamente bajo concesión.')

    # ------------------------------------------------------------------
    # Cómputos
    # ------------------------------------------------------------------

    def _compute_display_label(self):
        for rec in self:
            rec.display_label = '%s - %s' % (
                rec.production_id.name or '', rec.lot_number or '')

    @api.model
    def _release_gate_field_exists(self):
        """El campo de liberación solo existe si el módulo de Calidad está
        instalado. Sin él no hay concepto de liberación (dependencia suave,
        mismo patrón que el resto del módulo)."""
        return 'amunet_lot_release_state' in self.env['stock.lot']._fields

    @api.depends('lot_id')
    def _compute_sin_liberacion(self):
        tiene_calidad = self._release_gate_field_exists()
        for rec in self:
            if not tiene_calidad or not rec.lot_id:
                rec.sin_liberacion = False
                continue
            rec.sin_liberacion = (
                getattr(rec.lot_id, 'amunet_lot_release_state', 'released')
                != 'released')

    @api.depends('sin_liberacion', 'authorized_by')
    def _compute_vendible(self):
        for rec in self:
            rec.vendible = (not rec.sin_liberacion) or bool(rec.authorized_by)

    # ------------------------------------------------------------------
    # Candados de cantidad
    # ------------------------------------------------------------------

    @api.constrains('quantity_delivered')
    def _check_quantity_delivered(self):
        for rec in self:
            if rec.state == 'cancelada':
                continue
            if not rec.quantity_delivered or rec.quantity_delivered <= 0:
                raise ValidationError(_(
                    'La cantidad entregada debe ser mayor que cero.'))

    @api.model
    def _delivered_qty_for_lot(self, lot, exclude_id=None):
        """Piezas ya entregadas de un lote que siguen contando.

        Cuentan las entregas 'por recibir' y 'recibida'; las rechazadas y
        canceladas NO, porque su material vuelve a quedar pendiente.
        """
        if not lot:
            return 0.0
        domain = [
            ('lot_id', '=', lot.id),
            ('state', 'in', ('por_recibir', 'recibida')),
        ]
        if exclude_id:
            domain.append(('id', '!=', exclude_id))
        return sum(self.sudo().search(domain).mapped('quantity_delivered'))

    @api.model
    def _pending_qty_for_lot(self, lot, backend=None, exclude_id=None):
        """Piezas del lote que todavía se pueden entregar.

        Es la existencia LIBRE del lote en la ubicación de piezas de APT menos
        lo ya entregado y no rechazado. Evita entregar (y por tanto recibir)
        más piezas de las que existen: es el candado que faltaba y por el que
        un lote de 265 pz llegó a "recibirse" 795 veces.
        """
        if not lot:
            return 0.0
        # La configuración de la tienda es de administradores; el sistema la
        # lee con sudo para no exigirle permisos de admin a Acondicionado.
        backend = (backend or self._backend_for_product(lot.product_id)).sudo()
        if not backend:
            return 0.0
        libre = backend._apt_released_qty_for_lot(lot)
        return libre - self._delivered_qty_for_lot(lot, exclude_id=exclude_id)

    @api.model
    def _backend_for_product(self, product):
        """Tienda que corresponde a un producto.

        Se resuelve por su mapeo CONFIRMADO; si no lo tiene, se usa la primera
        tienda activa. Importa resolverla por producto y no "la primera que
        haya": cada tienda define su propia ubicación de piezas de APT, y
        tomar la equivocada haría que la existencia se lea como cero.
        """
        if product:
            mapping = self.env['amunet.woo.product.mapping'].sudo().search([
                ('relation_state', '=', 'confirmed'),
                ('product_id', '=', product.id),
            ], limit=1)
            if mapping.backend_id:
                return mapping.backend_id
        return self._default_backend()

    @api.model
    def _default_backend(self):
        """Tienda activa con la que se opera (la primera configurada)."""
        return self.env['amunet.woo.backend'].sudo().search(
            [('active', '=', True)], order='sequence, id', limit=1)

    # ------------------------------------------------------------------
    # Resolución del lote desde la orden de fabricación
    # ------------------------------------------------------------------

    @api.model
    def _resolve_lot_from_production(self, production):
        """Lote que produce una orden de fabricación.

        Odoo 19 no tiene ``lot_producing_id``. Se resuelve, en orden:
        1) ``lot_producing_ids`` de la orden,
        2) el lote de los movimientos de producto terminado,
        3) por convención de Amunet, el lote cuyo NOMBRE es el mismo que el de
           la orden (la orden ES el lote).
        """
        if not production:
            return self.env['stock.lot']
        lots = production.sudo().mapped('lot_producing_ids')
        lots = lots.filtered(lambda l: l.product_id == production.product_id)
        if lots:
            return lots[0]
        moves = production.sudo().move_finished_ids.filtered(
            lambda m: m.product_id == production.product_id)
        lots = moves.mapped('move_line_ids.lot_id')
        if lots:
            return lots[0]
        return self.env['stock.lot'].sudo().search([
            ('name', '=', production.name),
            ('product_id', '=', production.product_id.id),
        ], limit=1)

    # ------------------------------------------------------------------
    # Alta
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            production = self.env['mrp.production'].browse(
                vals['production_id']) if vals.get('production_id') else None
            if production:
                vals.setdefault('product_id', production.product_id.id)
                if not vals.get('lot_id'):
                    lot = self._resolve_lot_from_production(production)
                    if lot:
                        vals['lot_id'] = lot.id
            lot = self.env['stock.lot'].browse(vals['lot_id']) \
                if vals.get('lot_id') else None
            if lot:
                vals.setdefault('lot_number', lot.name)
                if lot.expiration_date:
                    vals.setdefault('expiration_month',
                                    lot.expiration_date.month)
                    vals.setdefault('expiration_year',
                                    lot.expiration_date.year)
        records = super().create(vals_list)
        for rec in records:
            rec._check_no_sobreentrega()
            rec.message_post(body=_(
                'ENTREGA registrada (%(tipo)s): %(qty)s pza(s) del lote '
                '%(lot)s por %(user)s.',
                tipo=dict(self._fields['tipo'].selection).get(rec.tipo),
                qty=rec.quantity_delivered, lot=rec.lot_number or '',
                user=rec.delivered_by.display_name))
            if rec.sin_liberacion:
                rec.message_post(body=_(
                    '<b>ATENCIÓN: material entregado SIN LIBERACIÓN DE '
                    'CALIDAD.</b> Se puede recibir físicamente, pero NO es '
                    'vendible mientras Calidad no libere el lote o alguien '
                    'con facultad lo autorice expresamente (concesión).'))
        return records

    def _check_no_sobreentrega(self):
        """Impide entregar más piezas de las que quedan pendientes del lote."""
        for rec in self:
            if rec.state in ('rechazada', 'cancelada') or not rec.lot_id:
                continue
            pendiente = self._pending_qty_for_lot(
                rec.lot_id, exclude_id=rec.id)
            # 'pendiente' ya excluye esta entrega, asi que se compara directo.
            if rec.quantity_delivered > pendiente + 0.0001:
                raise UserError(_(
                    'No se pueden entregar %(pide)s pza(s) del lote %(lot)s: '
                    'solo quedan %(quedan)s pendientes por entregar en el '
                    'almacén de piezas de APT.',
                    pide=rec.quantity_delivered, lot=rec.lot_number or '',
                    quedan=max(pendiente, 0.0)))

    # ------------------------------------------------------------------
    # Acciones de Acondicionado
    # ------------------------------------------------------------------

    @api.model
    def _crear_desde_produccion(self, production, tipo, quantity=None):
        """Crea la entrega desde una orden de fabricación."""
        lot = self._resolve_lot_from_production(production)
        if not lot:
            raise UserError(_(
                'La orden %s todavía no tiene lote de producto terminado. '
                'Producción debe registrar el lote antes de entregarlo.')
                % production.name)
        if tipo == 'completa':
            quantity = self._pending_qty_for_lot(lot)
            if quantity <= 0:
                raise UserError(_(
                    'El lote %s no tiene piezas pendientes por entregar en el '
                    'almacén de piezas de APT.') % lot.name)
        return self.create({
            'production_id': production.id,
            'tipo': tipo,
            'quantity_delivered': quantity,
            'lot_id': lot.id,
            'product_id': production.product_id.id,
        })

    def action_recibir(self):
        """El almacén confirma lo que contó.

        Si coincide con lo entregado, la entrega queda RECIBIDA y se genera la
        recepción para venta. Si NO coincide, se RECHAZA COMPLETA: no se acepta
        a medias, se aclara primero.
        """
        for rec in self:
            if rec.state != 'por_recibir':
                raise UserError(_(
                    'Solo se puede recibir una entrega que esté "Por recibir".'))
            if not rec.quantity_received or rec.quantity_received <= 0:
                raise UserError(_(
                    'Captura cuántas piezas contaste físicamente antes de '
                    'confirmar la recepción.'))
            if abs(rec.quantity_received - rec.quantity_delivered) > 0.0001:
                rec._rechazar(_(
                    'Diferencia entre lo entregado (%(ent)s) y lo contado por '
                    'almacén (%(rec)s). La entrega se rechaza completa para '
                    'aclararla.',
                    ent=rec.quantity_delivered, rec=rec.quantity_received))
                continue
            reception = self.env['amunet.woo.reception'].create({
                'backend_id': rec._backend().id,
                'company_id': rec.company_id.id,
                'product_id': rec.product_id.id,
                'lot_id': rec.lot_id.id,
                'quantity': rec.quantity_received,
                'delivery_id': rec.id,
            })
            rec.write({
                'state': 'recibida',
                'received_by': self.env.user.id,
                'received_date': fields.Datetime.now(),
                'reception_id': reception.id,
            })
            rec.message_post(body=_(
                'RECEPCIÓN confirmada por %(user)s: %(qty)s pza(s). '
                'Coincide con lo entregado.',
                user=self.env.user.display_name, qty=rec.quantity_received))
            if not rec.vendible:
                rec.message_post(body=_(
                    'El material queda RETENIDO (no vendible): el lote no '
                    'está liberado por Calidad y la entrega no tiene '
                    'autorización.'))
        return True

    def _backend(self):
        self.ensure_one()
        backend = self._backend_for_product(self.product_id)
        if not backend:
            raise UserError(_(
                'No hay una tienda configurada para registrar la recepción.'))
        return backend.sudo()

    def _rechazar(self, motivo):
        self.ensure_one()
        self.write({
            'state': 'rechazada',
            'rejection_reason': motivo,
            'received_by': self.env.user.id,
            'received_date': fields.Datetime.now(),
        })
        self.message_post(body=_(
            'ENTREGA RECHAZADA por %(user)s. %(motivo)s',
            user=self.env.user.display_name, motivo=motivo))

    def action_rechazar(self):
        """Rechazo manual de la entrega por el almacén."""
        for rec in self:
            if rec.state != 'por_recibir':
                raise UserError(_(
                    'Solo se puede rechazar una entrega que esté "Por recibir".'))
            rec._rechazar(rec.rejection_reason or _(
                'Rechazada por el almacén al recibir.'))
        return True

    def action_cancelar(self):
        for rec in self:
            if rec.state == 'recibida':
                raise UserError(_(
                    'La entrega del lote %s ya fue recibida; no puede '
                    'cancelarse.') % (rec.lot_number or ''))
            rec.state = 'cancelada'
            rec.message_post(body=_('Entrega cancelada por %s.')
                             % self.env.user.display_name)
        return True

    # ------------------------------------------------------------------
    # Autorización (liberación bajo concesión)
    # ------------------------------------------------------------------

    def action_autorizar(self):
        """Autoriza vender material que Calidad todavía no ha liberado.

        Solo para quien tenga el grupo ``group_woo_autoriza_concesion``
        (Mery/PM y Calidad). Queda registrado con nombre y fecha: es una
        liberación bajo CONCESIÓN (ISO 13485 8.3), no un salto silencioso del
        control de Calidad.
        """
        if not self.env.user.has_group(
                'amunet_woocommerce.group_woo_autoriza_concesion'):
            raise UserError(_(
                'No tienes facultad para autorizar la venta de material sin '
                'liberación de Calidad. Esta autorización la da PM (Mery) o '
                'Calidad.'))
        for rec in self:
            if not rec.sin_liberacion:
                raise UserError(_(
                    'El lote %s ya está liberado por Calidad; no necesita '
                    'autorización.') % (rec.lot_number or ''))
            if rec.authorized_by:
                raise UserError(_(
                    'La entrega del lote %s ya estaba autorizada por %s.')
                    % (rec.lot_number or '', rec.authorized_by.display_name))
            rec.write({
                'authorized_by': self.env.user.id,
                'authorized_date': fields.Datetime.now(),
            })
            rec.message_post(body=_(
                '<b>LIBERACIÓN BAJO CONCESIÓN.</b> %(user)s autorizó vender '
                'el lote %(lot)s SIN la liberación de Calidad. Motivo: '
                '%(motivo)s<br/>Calidad debe enterarse y regularizarlo: el '
                'material se publicará como vendible bajo esta autorización.',
                user=self.env.user.display_name, lot=rec.lot_number or '',
                motivo=rec.authorization_note or _('(sin motivo capturado)')))
            # La recepción ya generada pasa a vendible: se intenta publicar.
            if rec.reception_id:
                rec.reception_id._try_auto_publish()
        return True
