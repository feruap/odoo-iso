# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class AmunetLotFactory(models.Model):
    _name = 'amunet.lot.factory'
    _description = 'Lote de Fábrica'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, name'

    name = fields.Char(
        string='Número de serie/lote fábrica',
        required=True,
        index=True,
        tracking=True,
        help='Número de lote asignado por el fabricante'
    )

    ref = fields.Char(
        string='Referencia',
        tracking=True,
        help='Referencia adicional del lote de fábrica'
    )

    # Relación inversa: Un lote de fábrica puede tener múltiples lotes Amunet
    lot_ids = fields.One2many(
        'stock.lot',
        'factory_lot_id',
        string='Números de serie/lotes Amunet',
        help='Números de serie/lotes Amunet relacionados con este lote de fábrica'
    )

    lot_count = fields.Integer(
        string='Cantidad de lotes',
        compute='_compute_lot_count',
        store=True
    )

    @api.depends('lot_ids')
    def _compute_lot_count(self):
        """Calcula el número de números de serie/lotes Amunet asociados"""
        for factory_lot in self:
            factory_lot.lot_count = len(factory_lot.lot_ids)

    def action_view_lots(self):
        """Acción para ver los números de serie/lotes Amunet asociados"""
        self.ensure_one()
        return {
            'name': _('Números de serie/lotes Amunet'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.lot',
            'view_mode': 'tree,form',
            'domain': [('factory_lot_id', '=', self.id)],
            'context': {
                'default_factory_lot_id': self.id,
            }
        }

    _name_uniq = models.Constraint(
        'unique (name)',
        'El número de serie/lote de fábrica debe ser único.',
    )
