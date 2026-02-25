# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    
    # ============================================================================
    # Campo factory_lot_id - Restaurado con solución definitiva
    # ============================================================================
    factory_lot_id = fields.Many2one(
        'amunet.lot.factory',
        string='Número de serie/lote de fábrica',
        help='Número de serie/lote de fábrica asociado a este lote Amunet. Se puede asignar desde la vista de operaciones.',
        copy=True,
    )
    
    # ============================================================================
    # Campo manufacturing_date - Para Control de Calidad
    # ============================================================================
    manufacturing_date = fields.Date(
        string='Fecha de fabricación',
        help='Fecha de fabricación del producto. Se sincroniza al control de calidad.',
        copy=True,
        tracking=True,
    )
    
    @api.onchange('lot_id')
    def _onchange_lot_id_factory(self):
        """
        Carga factory_lot_id desde lot_id cuando se selecciona un lote.

        SOLUCIÓN: Solo carga, no modifica lot_id.
        """
        if self.lot_id and self.lot_id.factory_lot_id:
            self.factory_lot_id = self.lot_id.factory_lot_id

    @api.model_create_multi
    def create(self, vals_list):
        """
        Sincronización de factory_lot_id y fechas entre stock.move.line y stock.lot.
        """
        date_fields = ['expiration_date', 'removal_date', 'manufacturing_date']
        
        for vals in vals_list:
            lot_id = vals.get('lot_id')
            factory_lot_id = vals.get('factory_lot_id')
            
            if lot_id and not factory_lot_id:
                # Cargar factory_lot_id desde el lote
                lot = self.env['stock.lot'].browse(lot_id)
                if lot.exists() and lot.factory_lot_id:
                    vals['factory_lot_id'] = lot.factory_lot_id.id
            
            # --- CORRECCIÓN GENERACIÓN DE LOTES AMUNET ---
            # Si se intenta crear una línea con lot_name="0" (fallo del widget nativo) 
            # o sin lot_name para un producto Amunet, interceptamos y generamos.
            product_id = vals.get('product_id')
            lot_name = vals.get('lot_name')
            lot_id_chk = vals.get('lot_id')
            
            if product_id and not lot_id_chk and (not lot_name or lot_name == '0'):
                product = self.env['product.product'].browse(product_id)
                # Verificar si es producto Amunet con secuencia
                if product.lot_sequence_id:
                    # Generar siguiente
                    next_lot = product.lot_sequence_id.next_by_id()
                    vals['lot_name'] = next_lot
                    # Asegurar quantity 1.0 si no está
                    if not vals.get('quantity') and not vals.get('qty_done'):
                        vals['quantity'] = 1.0
        
        records = super().create(vals_list)
        
        # Sincronizar campos al lote y REFORZAR los valores en la línea
        for record, vals in zip(records, vals_list):
            if record.lot_id:
                vals_sync = {f: vals[f] for f in date_fields if vals.get(f)}
                
                # Sincronizar factory_lot_id si no lo tiene el lote
                if record.factory_lot_id and not record.lot_id.factory_lot_id:
                    vals_sync['factory_lot_id'] = record.factory_lot_id.id
                
                if vals_sync:
                    # 1. Al lote
                    record.lot_id.sudo().write(vals_sync)
                    
                    # 2. Refuerzo a la línea (evita resets de product_expiry)
                    line_update = {f: v for f, v in vals_sync.items() if record[f] != v}
                    if line_update:
                        super(StockMoveLine, record).write(line_update)
        
        return records

    def _prepare_new_lot_vals(self):
        """
        PREPARACIÓN DE VALORES PARA NUEVOS LOTES
        Aseguramos que las fechas ingresadas en la línea se pasen al lote
        al momento de su creación durante la validación.
        """
        vals = super()._prepare_new_lot_vals()
        
        # Sincronizar fechas si están presentes en la línea
        if self.expiration_date:
            vals['expiration_date'] = self.expiration_date
        if self.removal_date:
            vals['removal_date'] = self.removal_date
        if self.manufacturing_date:
            vals['manufacturing_date'] = self.manufacturing_date
        if self.factory_lot_id:
            vals['factory_lot_id'] = self.factory_lot_id.id
            
        return vals

    def write(self, vals):
        """
        Sincronización bidireccional de campos entre stock.move.line y stock.lot.
        + Corrección de lotes Amunet generados como '0'.
        """
        date_fields = ['expiration_date', 'removal_date', 'manufacturing_date']
        
        # --- CORRECCIÓN WRITE ---
        if vals.get('lot_name') == '0' and len(self) == 1:
            if self.product_id.lot_sequence_id:
                vals['lot_name'] = self.product_id.lot_sequence_id.next_by_id()
                
        # Interceptar campos de fecha para sincronización forzada
        sync_vals = {f: vals[f] for f in date_fields if f in vals}

        if 'lot_id' in vals and 'factory_lot_id' not in vals:
            lot_id = vals.get('lot_id')
            if lot_id:
                lot = self.env['stock.lot'].browse(lot_id)
                if lot.exists() and lot.factory_lot_id:
                    vals['factory_lot_id'] = lot.factory_lot_id.id
        
        res = super().write(vals)
        
        # Sincronizar al lote después de la escritura
        if sync_vals:
            for record in self:
                if record.lot_id:
                    # 1. Al lote
                    record.lot_id.sudo().write(sync_vals)
                
                # 2. Refuerzo a la línea (evita resets de product_expiry)
                line_update = {f: v for f, v in sync_vals.items() if record[f] != v}
                if line_update:
                    super(StockMoveLine, record).write(line_update)
        
        # Sincronización adicional post-super personalizada (para cambios de factory_lot_id)
        for record in self:
            if record.lot_id:
                vals_after = {}
                if record.factory_lot_id and record.lot_id.factory_lot_id != record.factory_lot_id:
                    vals_after['factory_lot_id'] = record.factory_lot_id.id
                
                if vals_after:
                    record.lot_id.sudo().write(vals_after)
        
        return res
    
    def _sync_factory_lot_to_stock_lot(self):
        """
        Método para sincronizar factory_lot_id de las líneas a los lotes.
        Se puede llamar manualmente o desde la validación del picking.
        """
        for record in self:
            if record.factory_lot_id and record.lot_id:
                if record.lot_id.factory_lot_id != record.factory_lot_id:
                    record.lot_id.sudo().write({'factory_lot_id': record.factory_lot_id.id})
    
    def action_generate_factory_lots(self):
        """Acción de botón para generar lotes de fábrica."""
        if not self:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sin líneas seleccionadas'),
                    'message': _('Seleccione al menos una línea para generar lotes de fábrica.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }
        return self.env['stock.move'].generate_factory_lots_for_lines(self.ids)
