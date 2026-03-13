# -*- coding: utf-8 -*-

from odoo import models


class StockPickingType(models.Model):
    """
    Override de stock.picking.type para que la gráfica del dashboard
    de inventario sea visible para todos los usuarios, no solo admins.

    Epic-033: Control de Acceso Dinámico por Almacén
    """
    _inherit = 'stock.picking.type'

    def _get_aggregated_records_by_date(self):
        """
        Override para usar sudo() al leer stock.picking, de modo que todos
        los usuarios vean los datos reales del almacén en el kanban dashboard,
        independientemente de sus permisos individuales de lectura.
        """
        records = self.sudo().env['stock.picking']._read_group(
            [
                ('picking_type_id', 'in', self.ids),
                ('state', 'in', ['assigned', 'waiting', 'confirmed'])
            ],
            ['picking_type_id'],
            ['scheduled_date:array_agg'],
        )
        picking_type_id_to_dates = {i: [] for i in self.ids}
        picking_type_id_to_dates.update({r[0].id: r[1] for r in records})
        return [(i, d, self.env._('Transfers')) for i, d in picking_type_id_to_dates.items()]
