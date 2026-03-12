# -*- coding: utf-8 -*-
from odoo import models, fields, api


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

    # Campo manufacturing_date - Sincronizado desde la línea
    manufacturing_date = fields.Date(
        string='Fecha de fabricación',
        help='Fecha de fabricación del lote, sincronizada desde el movimiento de inventario.',
        tracking=True,
    )

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
