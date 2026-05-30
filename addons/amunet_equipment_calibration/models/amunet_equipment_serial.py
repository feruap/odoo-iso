# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AmunetEquipmentSerial(models.Model):
    """Serie de un equipo fisico capturada bajo un lote Amunet.

    Patron: para productos de equipos (EQ*) marcados con
    `amunet_allow_multi_serial=True`, un solo lote Amunet (stock.lot)
    agrupa varias unidades fisicas. Cada unidad tiene su numero de serie
    del fabricante registrado aqui. Asi evitamos crear un lote por cada
    unidad y mantenemos trazabilidad de pieza individual.
    """
    _name = 'amunet.equipment.serial'
    _description = 'Serie de equipo bajo lote Amunet'
    _order = 'lot_id, serial_number'

    lot_id = fields.Many2one(
        'stock.lot',
        string='Lote Amunet',
        required=True,
        ondelete='cascade',
        index=True,
    )
    product_id = fields.Many2one(
        'product.product',
        related='lot_id.product_id',
        store=True,
        readonly=True,
    )
    serial_number = fields.Char(
        string='Numero de serie',
        required=True,
        index=True,
        help='Numero de serie del fabricante para esta unidad fisica.',
    )
    notes = fields.Text(string='Notas')
    active = fields.Boolean(default=True)

    _unique_serial_per_lot = models.Constraint(
        'unique(lot_id, serial_number)',
        'El numero de serie no puede repetirse dentro del mismo lote Amunet.',
    )

    @api.constrains('lot_id')
    def _check_product_allows_multi_serial(self):
        for rec in self:
            tmpl = rec.lot_id.product_id.product_tmpl_id
            if tmpl and not tmpl.amunet_allow_multi_serial:
                raise ValidationError(_(
                    'El producto "%s" no esta configurado para series '
                    'multiples. Activa "Permite multiples series por '
                    'lote" en la ficha del producto.'
                ) % tmpl.display_name)
