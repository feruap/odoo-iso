# -*- coding: utf-8 -*-
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

    @api.onchange('expiration_date')
    def _onchange_expiration_date_amunet(self):
        """
        Calcula automáticamente la fecha de remoción 2 meses antes de la caducidad.
        Si cae en el pasado, la iguala a la fecha de caducidad.
        Si se borra la caducidad, se borra la remoción.
        """
        if not self.expiration_date:
            self.removal_date = False
            return

        from dateutil.relativedelta import relativedelta
        from odoo import fields as odoo_fields
        
        calculated_removal = self.expiration_date - relativedelta(months=2)
        today = odoo_fields.Date.context_today(self)
        
        # Convertir a date para comparación si es datetime
        calculated_date = calculated_removal.date() if hasattr(calculated_removal, 'date') else calculated_removal

        if calculated_date < today:
            self.removal_date = self.expiration_date
        else:
            self.removal_date = calculated_removal
