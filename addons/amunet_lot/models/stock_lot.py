# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _


class StockLot(models.Model):
    _inherit = 'stock.lot'
    
    # Campo para indicar si el lote fue generado automáticamente
    amunet_auto_generated = fields.Boolean(
        string='Generado automáticamente',
        default=False,
        readonly=True,
        help="Indica si este lote fue generado automáticamente por el sistema"
    )
    
    # Relación con lote de fábrica
    factory_lot_id = fields.Many2one(
        'amunet.lot.factory',
        string='Número de serie/lote de fábrica',
        index=True,
        ondelete='restrict',
        help='Número de serie/lote de fábrica asociado a este Número de serie/lote de Amunet'
    )

    analysis_number = fields.Char(
        string='No. Análisis',
        help='Número de análisis asociado a este lote.',
        tracking=True,
    )

    # Campo manufacturing_date - Sincronizado desde la línea
    manufacturing_date = fields.Date(
        string='Fecha de fabricación',
        help='Fecha de fabricación del lote, sincronizada desde el movimiento de inventario.',
        tracking=True,
    )

    # Ubicacion legible para la lista de lotes: muestra el nombre del
    # lugar si el lote esta en una sola ubicacion, o "Varias ubicaciones"
    # si esta repartido en mas de una. El campo nativo location_id queda
    # vacio cuando hay multiples ubicaciones, lo que confunde al usuario.
    amunet_ubicacion_display = fields.Char(
        string='Ubicación',
        compute='_compute_amunet_ubicacion_display',
        help='Ubicación del lote: el nombre del lugar si está en uno solo, '
             'o "Varias ubicaciones" si su existencia está repartida.',
    )

    @api.depends('quant_ids.quantity', 'quant_ids.location_id')
    def _compute_amunet_ubicacion_display(self):
        for lot in self:
            locs = lot.quant_ids.filtered(
                lambda q: q.quantity > 0
                and q.location_id.usage in ('internal', 'transit')
            ).location_id
            if len(locs) == 1:
                lot.amunet_ubicacion_display = locs.complete_name
            elif len(locs) > 1:
                lot.amunet_ubicacion_display = _('Varias ubicaciones')
            else:
                lot.amunet_ubicacion_display = ''

    def _amunet_removal_from_expiration(self, expiration, product=None):
        """Fecha de remocion = caducidad - anticipo configurado en la CATEGORIA
        del producto (Materia prima=1 mes, Soluciones=7 dias, Terminados=4 meses;
        default 1 mes). Si el resultado cae en el pasado, se iguala a la caducidad
        (no tiene sentido una remocion anterior a hoy). False si no hay caducidad.
        """
        if not expiration:
            return False
        expiration = fields.Datetime.to_datetime(expiration)
        if product is None:
            product = self.product_id if self else False
        value, unit = 1, 'months'
        categ = product.categ_id if product else False
        if categ:
            value, unit = categ._amunet_get_removal_offset()
        delta = relativedelta(months=value) if unit == 'months' else relativedelta(days=value)
        calculated_removal = expiration - delta
        today = fields.Date.context_today(self)
        calculated_date = calculated_removal.date() if hasattr(calculated_removal, 'date') else calculated_removal
        if calculated_date < today:
            return expiration
        return calculated_removal

    @api.onchange('expiration_date')
    def _onchange_expiration_date_amunet(self):
        """En el formulario: al poner/cambiar la caducidad, calcula la remocion
        segun la categoria del producto. Si se borra la caducidad, se borra."""
        self.removal_date = self._amunet_removal_from_expiration(
            self.expiration_date, product=self.product_id)

    @api.model_create_multi
    def create(self, vals_list):
        """Aplica la remocion automatica tambien cuando el lote se crea por
        codigo/importacion/auto-generacion (el onchange solo corre en la UI).
        Respeta una remocion provista explicitamente en los mismos vals."""
        for vals in vals_list:
            if vals.get('expiration_date') and not vals.get('removal_date'):
                product = (self.env['product.product'].browse(vals['product_id'])
                           if vals.get('product_id') else False)
                vals['removal_date'] = self._amunet_removal_from_expiration(
                    vals['expiration_date'], product=product)
        return super().create(vals_list)

    def write(self, vals):
        """Al cambiar la caducidad por codigo/UI, recalcula la remocion segun la
        categoria, salvo que se escriba una remocion explicita a la vez."""
        res = super().write(vals)
        if 'expiration_date' in vals and 'removal_date' not in vals:
            for lot in self:
                nueva = lot._amunet_removal_from_expiration(
                    lot.expiration_date, product=lot.product_id)
                if lot.removal_date != nueva:
                    super(StockLot, lot).write({'removal_date': nueva})
        return res
