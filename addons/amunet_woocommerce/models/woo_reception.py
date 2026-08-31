# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AmunetWooReception(models.Model):
    """Recepción de material para venta (almacén woolibre).

    Registra la ACEPTACIÓN por parte del almacén de producto terminado de que
    un lote (o una parte de él) se recibe para venta en la tienda. Es el paso
    que faltaba entre la LIBERACIÓN de Calidad y la publicación a la tienda:

        Producción/Compra -> Calidad LIBERA el lote -> el almacén ACEPTA la
        recepción (aquí) -> se publica como existencia vendible (Woo disponible).

    Reglas regulatorias (ISO 13485, 7.5.5 Preservación / 7.5.1 liberación):
    - Solo puede recibirse material que Calidad haya LIBERADO
      (``amunet_lot_release_state == 'released'``). El candado es duro.
    - Las entregas parciales son normales: un lote puede recibirse en varias
      aceptaciones; cada una es un evento auditable e independiente y se publica
      una sola vez (idempotencia por recepción).

    Este modelo es la fuente de verdad de "lo recibido para venta": la
    publicación a la tienda se dispara desde aquí, no desde la liberación.
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
    state = fields.Selection([
        ('aceptada', 'Aceptada'),
        ('publicada', 'Publicada'),
        ('cancelada', 'Cancelada'),
    ], string='Estado', default='aceptada', required=True, tracking=True)
    notes = fields.Text(string='Notas')
    sync_log_id = fields.Many2one(
        'amunet.woo.sync.log', string='Bitácora', ondelete='set null')

    # ------------------------------------------------------------------
    # Candados (calidad + cantidad)
    # ------------------------------------------------------------------

    @api.model
    def _release_gate_field_exists(self):
        """El campo de liberación solo existe si el módulo de Calidad está
        instalado. Si no está, no hay concepto de liberación y no se bloquea
        (mismo patrón de dependencia suave del resto del módulo)."""
        return 'amunet_lot_release_state' in self.env['stock.lot']._fields

    @api.constrains('lot_id', 'state')
    def _check_release_gate(self):
        """Candado duro: no se acepta recepción de un lote no liberado."""
        if not self._release_gate_field_exists():
            return
        for rec in self:
            if rec.state == 'cancelada' or not rec.lot_id:
                continue
            if rec.lot_id.amunet_lot_release_state != 'released':
                raise UserError(_(
                    'No puedes aceptar la recepción del lote %(lot)s: Calidad '
                    'aún no lo ha liberado. Primero debe liberarse por Calidad '
                    'y después el almacén acepta la recepción.',
                    lot=rec.lot_id.name or rec.lot_number or ''))

    @api.constrains('quantity')
    def _check_quantity(self):
        for rec in self:
            if rec.quantity is not None and rec.quantity <= 0:
                raise ValidationError(_(
                    'La cantidad recibida debe ser mayor que cero.'))

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
            rec._try_auto_publish()
        return records

    def _try_auto_publish(self):
        """Intenta publicar la recepción a la tienda si la publicación está
        habilitada. NUNCA lanza excepción: aceptar la recepción no debe fallar
        porque la tienda no responda o no esté configurada."""
        self.ensure_one()
        if self.state != 'aceptada':
            return
        backend = self.backend_id
        if not backend or not backend.allow_stock_publish:
            return
        if not backend.apt_wp_user or not backend.apt_wp_app_password:
            return
        try:
            with self.env.cr.savepoint():
                backend.sudo()._publicar_recepciones(self)
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
