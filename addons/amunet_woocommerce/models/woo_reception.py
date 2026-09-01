# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AmunetWooReception(models.Model):
    """Recepción de material para venta (almacén woolibre).

    Registra que el almacén de producto terminado RECIBIÓ material y con qué
    cantidad. Es el segundo de los dos pasos del flujo de entrega:

        Acondicionado ENTREGA (``amunet.woo.delivery``)
            -> el ALMACÉN cuenta y RECIBE (aquí)
            -> si es vendible, se publica a la tienda (Woo disponible).

    Recibir NO es lo mismo que poder vender (ISO 13485)
    ---------------------------------------------------
    Recibir físicamente material que Calidad todavía no ha liberado SÍ está
    permitido: pasa en la operación cuando el material urge. Lo que NO está
    permitido es venderlo. Por eso aquí no hay candado que impida recibir; el
    candado está en la PUBLICACIÓN:

    - lote liberado por Calidad                       -> vendible;
    - lote sin liberar pero con entrega AUTORIZADA    -> vendible bajo
      concesión (ISO 13485 8.3), con el autorizante registrado;
    - lote sin liberar y sin autorización             -> RETENIDO: se recibe,
      pero no se publica a la tienda.

    Las entregas parciales son normales: un lote se recibe en varias
    aceptaciones; cada una es un evento auditable e independiente y se publica
    una sola vez (idempotencia por recepción).
    """

    _name = 'amunet.woo.reception'
    _description = 'Recepción de material para venta (woolibre)'
    _inherit = ['mail.thread']
    _order = 'id desc'

    backend_id = fields.Many2one(
        'amunet.woo.backend', string='Tienda',
        required=True, ondelete='restrict', index=True)
    company_id = fields.Many2one(
        'res.company', string='Compañía', required=True,
        default=lambda self: self.env.company, index=True)
    mapping_id = fields.Many2one(
        'amunet.woo.product.mapping', string='Mapeo',
        ondelete='set null', index=True)
    product_id = fields.Many2one(
        'product.product', string='Producto', ondelete='restrict', index=True)
    lot_id = fields.Many2one(
        'stock.lot', string='Lote', ondelete='restrict', index=True)
    lot_number = fields.Char(string='Número de lote')
    quantity = fields.Float(string='Piezas recibidas')
    expiration_month = fields.Integer(string='Mes de caducidad')
    expiration_year = fields.Integer(string='Año de caducidad')
    received_by = fields.Many2one(
        'res.users', string='Recibido por', readonly=True,
        default=lambda self: self.env.user, index=True)
    received_date = fields.Datetime(
        string='Fecha de recepción', readonly=True,
        default=fields.Datetime.now, required=True)
    delivery_id = fields.Many2one(
        'amunet.woo.delivery', string='Entrega de origen',
        ondelete='set null', index=True,
        help='Entrega de Acondicionado que originó esta recepción.')
    state = fields.Selection([
        ('aceptada', 'Aceptada'),
        ('publicada', 'Publicada'),
        ('cancelada', 'Cancelada'),
    ], string='Estado', default='aceptada', required=True, tracking=True)
    notes = fields.Text(string='Notas')
    sync_log_id = fields.Many2one(
        'amunet.woo.sync.log', string='Bitácora', ondelete='set null')

    # ------------------------------------------------------------------
    # Retenido vs vendible
    # ------------------------------------------------------------------

    sin_liberacion = fields.Boolean(
        string='SIN liberación de Calidad', compute='_compute_sin_liberacion',
        store=True, readonly=True)
    vendible = fields.Boolean(
        string='Vendible', compute='_compute_vendible', store=True,
        help='Vendible si el lote está liberado por Calidad, o si se autorizó '
             'expresamente (concesión), ya sea en la entrega de origen o en '
             'esta misma recepción. Si no, el material queda RETENIDO y no se '
             'publica a la tienda.')

    # Autorización propia de la recepción: sirve para REGULARIZAR material
    # histórico que entró antes de que existiera el flujo de entregas y que
    # por tanto no tiene ``delivery_id`` al que autorizar.
    authorized_by = fields.Many2one(
        'res.users', string='Autorizado por', readonly=True, index=True,
        tracking=True,
        help='Quien autorizó vender este material sin la liberación de '
             'Calidad (liberación bajo concesión, ISO 13485 8.3).')
    authorized_date = fields.Datetime(
        string='Fecha de autorización', readonly=True, tracking=True)
    authorization_note = fields.Text(
        string='Motivo de la autorización', tracking=True)
    requiere_regularizacion = fields.Boolean(
        string='Requiere regularización', compute='_compute_vendible',
        store=True,
        help='Material recibido sin liberación de Calidad y sin autorización: '
             'está retenido y alguien con facultad (PM/Calidad) debe '
             'regularizarlo.')

    @api.model
    def _release_gate_field_exists(self):
        """El campo de liberación solo existe si el módulo de Calidad está
        instalado. Si no está, no hay concepto de liberación (dependencia
        suave, mismo patrón del resto del módulo)."""
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

    @api.depends('sin_liberacion', 'authorized_by', 'state',
                 'delivery_id.authorized_by')
    def _compute_vendible(self):
        """Vendible por liberación de Calidad o por concesión autorizada.

        La concesión vale tanto si se autorizó en la ENTREGA de origen como si
        se autorizó en esta misma RECEPCIÓN: lo segundo es lo que permite
        regularizar material histórico que entró antes de existir el flujo de
        entregas y que por eso no tiene entrega a la cual autorizar.
        """
        for rec in self:
            if not rec.sin_liberacion:
                rec.vendible = True
            else:
                rec.vendible = bool(
                    rec.authorized_by or rec.delivery_id.authorized_by)
            rec.requiere_regularizacion = (
                rec.sin_liberacion and not rec.vendible
                and rec.state != 'cancelada')

    @api.constrains('quantity')
    def _check_quantity(self):
        for rec in self:
            if rec.quantity is not None and rec.quantity <= 0:
                raise ValidationError(_(
                    'La cantidad recibida debe ser mayor que cero.'))

    @api.constrains('lot_id', 'quantity', 'state')
    def _check_no_sobrerecepcion(self):
        """No se puede recibir más piezas de las que el lote tiene en APT.

        Este es el candado que faltaba: sin él, aceptar la recepción del mismo
        lote varias veces "recibía" 795 pz de un lote de 265.
        """
        for rec in self:
            if rec.state == 'cancelada' or not rec.lot_id:
                continue
            backend = rec.backend_id.sudo()
            if not backend:
                continue
            # Si no se puede resolver la ubicacion de piezas de APT no hay con
            # que medir: no se bloquea (una tienda mal configurada no debe
            # impedir registrar lo que el almacen ya recibio fisicamente).
            if not backend._apt_pieces_location():
                continue
            libre = backend._apt_released_qty_for_lot(rec.lot_id)
            recibido = sum(self.sudo().search([
                ('lot_id', '=', rec.lot_id.id),
                ('state', '!=', 'cancelada'),
            ]).mapped('quantity'))
            if recibido > libre + 0.0001:
                raise ValidationError(_(
                    'No se pueden recibir %(pide)s pza(s) del lote %(lot)s: '
                    'el almacén de piezas de APT solo tiene %(hay)s y ya se '
                    'habían recibido %(ya)s.',
                    pide=rec.quantity, lot=rec.lot_number or rec.lot_id.name,
                    hay=libre, ya=recibido - rec.quantity))

    # ------------------------------------------------------------------
    # Alta (rellena datos del lote) + auto-publicación segura
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        Lot = self.env['stock.lot']
        for vals in vals_list:
            lot = Lot.browse(vals['lot_id']) if vals.get('lot_id') else Lot
            if lot:
                vals.setdefault('lot_number', lot.name)
                if lot.product_id:
                    vals.setdefault('product_id', lot.product_id.id)
                if lot.expiration_date:
                    vals.setdefault('expiration_month', lot.expiration_date.month)
                    vals.setdefault('expiration_year', lot.expiration_date.year)
        records = super().create(vals_list)
        for rec in records:
            rec.message_post(body=_(
                'Recepción para venta ACEPTADA: %(qty)s pza(s) del lote '
                '%(lot)s por %(user)s.',
                qty=rec.quantity, lot=rec.lot_number or '',
                user=rec.received_by.display_name))
            if not rec.vendible:
                rec.message_post(body=_(
                    '<b>Material RETENIDO:</b> el lote no está liberado por '
                    'Calidad y no hay autorización. Se recibió físicamente, '
                    'pero NO se publica como existencia vendible.'))
            rec._try_auto_publish()
        return records

    def _try_auto_publish(self):
        """Intenta publicar la recepción a la tienda si procede.

        NUNCA lanza excepción: aceptar la recepción no debe fallar porque la
        tienda no responda o no esté configurada. Solo publica material
        VENDIBLE (liberado por Calidad o autorizado bajo concesión).
        """
        self.ensure_one()
        if self.state != 'aceptada':
            return
        if not self.vendible:
            return
        # Los candados y credenciales de la tienda son campos reservados a
        # administradores; el almacen no tiene por que verlos. Se leen con sudo
        # de forma interna: aceptar una recepcion NO debe exigir ser admin.
        backend = self.backend_id.sudo()
        if not backend or not backend.allow_stock_publish:
            return
        if not backend.apt_wp_user or not backend.apt_wp_app_password:
            return
        try:
            with self.env.cr.savepoint():
                backend._publicar_recepciones(self)
        except Exception:  # noqa: BLE001 - jamás debe propagar
            _logger.exception(
                'Auto-publicación de recepción a la tienda falló (ignorado)')

    # ------------------------------------------------------------------
    # Acciones de UI
    # ------------------------------------------------------------------

    def action_cancelar(self):
        for rec in self:
            if rec.state == 'publicada':
                raise UserError(_(
                    'La recepción del lote %s ya se publicó a la tienda; no '
                    'puede cancelarse desde aquí.') % (rec.lot_number or ''))
            rec.state = 'cancelada'
        return True

    def action_autorizar(self):
        """REGULARIZA material retenido: autoriza venderlo sin liberación.

        Pensada para el material que entró ANTES de que existiera el flujo de
        entregas y que por eso no tiene ``delivery_id`` al cual autorizar (por
        ejemplo, piezas entregadas al almacén con el lote todavía en
        'pendiente' de Calidad). Funciona sobre una SELECCIÓN de la lista, para
        regularizar varias de una vez.

        Solo para quien tenga ``group_woo_autoriza_concesion`` (PM/Mery y
        Calidad). Queda registrado con nombre y fecha: es una liberación bajo
        CONCESIÓN (ISO 13485 8.3), no un salto silencioso del control.
        """
        if not self.env.user.has_group(
                'amunet_woocommerce.group_woo_autoriza_concesion'):
            raise UserError(_(
                'No tienes facultad para autorizar la venta de material sin '
                'liberación de Calidad. Esta autorización la da PM (Mery) o '
                'Calidad.'))
        ahora = fields.Datetime.now()
        autorizadas = self.browse()
        for rec in self:
            if rec.state == 'cancelada':
                raise UserError(_(
                    'La recepción del lote %s está cancelada; no se autoriza.')
                    % (rec.lot_number or ''))
            if not rec.sin_liberacion:
                raise UserError(_(
                    'El lote %s ya está liberado por Calidad; no necesita '
                    'autorización.') % (rec.lot_number or ''))
            if rec.authorized_by or rec.delivery_id.authorized_by:
                raise UserError(_(
                    'La recepción del lote %s ya estaba autorizada.')
                    % (rec.lot_number or ''))
            rec.write({
                'authorized_by': self.env.user.id,
                'authorized_date': ahora,
            })
            rec.message_post(body=_(
                '<b>LIBERACIÓN BAJO CONCESIÓN (regularización).</b> %(user)s '
                'autorizó vender %(qty)s pza(s) del lote %(lot)s SIN la '
                'liberación de Calidad. Motivo: %(motivo)s<br/>Calidad debe '
                'enterarse y regularizarlo: a partir de ahora el material '
                'cuenta como vendible bajo esta autorización.',
                user=self.env.user.display_name, qty=rec.quantity,
                lot=rec.lot_number or '',
                motivo=rec.authorization_note or _('(sin motivo capturado)')))
            autorizadas |= rec
        # Ya vendibles: se intenta publicar lo que estaba retenido.
        for rec in autorizadas:
            rec._try_auto_publish()
        return True
