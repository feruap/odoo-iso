# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.tools import format_datetime


class StockTraceabilityReport(models.TransientModel):
    _inherit = 'stock.traceability.report'

    def _make_dict_move(self, level, parent_id, move_line, unfoldable=False):
        """
        Override para agregar factory_lot_id al diccionario de datos.
        """
        # Obtener datos originales
        data = super()._make_dict_move(level, parent_id, move_line, unfoldable)

        # Agregar factory_lot_id al primer elemento del array
        if data and len(data) > 0:
            # Obtener factory_lot_id desde move_line
            factory_lot_name = False
            if hasattr(move_line, 'factory_lot_id') and move_line.factory_lot_id:
                factory_lot_name = move_line.factory_lot_id.name
            # Si no está en move_line, intentar desde lot_id
            elif move_line.lot_id and hasattr(move_line.lot_id, 'factory_lot_id') and move_line.lot_id.factory_lot_id:
                factory_lot_name = move_line.lot_id.factory_lot_id.name

            # Agregar al diccionario
            data[0]['factory_lot_name'] = factory_lot_name

        return data

    @api.model
    def _final_vals_to_lines(self, final_vals, level):
        """
        Override para agregar factory_lot_name a las columnas.
        Insertar ANTES de lot_name (Número de lote/serie Amunet).
        """
        lines = []
        for data in final_vals:
            lines.append({
                'id': self._autoIncrement(),
                'model': data['model'],
                'model_id': data['model_id'],
                'parent_id': data['parent_id'],
                'usage': data.get('usage', False),
                'is_used': data.get('is_used', False),
                'lot_name': data.get('lot_name', False),
                'lot_id': data.get('lot_id', False),
                'factory_lot_name': data.get('factory_lot_name', False),
                'reference': data.get('reference_id', False),
                'location_source': data.get('location_source', False),
                'location_destination': data.get('location_destination', False),
                'partner_id': data.get('partner_id', False),
                'picking_type_code': data.get('picking_type_code', False),
                'res_id': data.get('res_id', False),
                'res_model': data.get('res_model', False),
                'columns': [
                    data.get('reference_id', False),
                    data.get('product_id', False),
                    format_datetime(self.env, data.get('date', False), tz=False, dt_format=False),
                    data.get('factory_lot_name', False),  # NUEVA COLUMNA
                    data.get('lot_name', False),
                    data.get('location_source', False),
                    data.get('location_destination', False),
                    data.get('product_qty_uom', 0)
                ],
                'level': level,
                'unfoldable': data['unfoldable'],
            })
        return lines

    def _autoIncrement(self):
        """Helper para mantener compatibilidad con autoIncrement global."""
        # Reutilizar la función global autoIncrement del módulo base
        from odoo.addons.stock.report.stock_traceability import autoIncrement
        return autoIncrement()
