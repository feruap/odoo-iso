# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AmunetQualityPoint(models.Model):
    """
    Puntos de Control de Calidad Configurable.
    Define qué parámetros se deben aplicar a qué productos y en qué operaciones.
    """
    _name = 'amunet.quality.point'
    _description = 'Punto de Control de Calidad'
    _order = 'name'

    name = fields.Char(string='Referencia', required=True)
    
    active = fields.Boolean(default=True)
    
    company_id = fields.Many2one(
        'res.company', string='Compañía', 
        default=lambda self: self.env.company, required=True
    )

    product_ids = fields.Many2many(
        'product.product', 
        string='Productos',
        help='Productos a los que se aplica este punto de control'
    )

    picking_type_ids = fields.Many2many(
        'stock.picking.type',
        string='Tipos de Operación',
        help='Operaciones donde se disparará el control de calidad'
    )

    parameter_ids = fields.Many2many(
        'amunet.quality.check.parameter',
        string='Parámetros de Calidad',
        help='Lista de parámetros que se cargarán en el QC automático'
    )

    parameter_product_rel_ids = fields.Many2many(
        'amunet.quality.parameter.product.rel',
        'amunet_quality_point_rel_personalization_rel',
        'point_id', 'rel_id',
        string='Personalización por Producto',
        compute='_compute_parameter_product_rel_ids',
        store=True,
        help='Permite personalizar los parámetros para cada producto vinculado'
    )

    @api.depends('product_ids', 'parameter_ids')
    def _compute_parameter_product_rel_ids(self):
        # 1. Recopilar todos los templates y parámetros de todos los registros para pre-carga
        all_tmpl_ids = self.product_ids.mapped('product_tmpl_id').ids
        all_param_codes = self.parameter_ids.mapped('code')
        
        if not all_tmpl_ids or not all_param_codes:
            for record in self:
                record.parameter_product_rel_ids = [(5, 0, 0)]
            return

        # 2. Una sola consulta para encontrar TODAS las relaciones potencialmente relevantes
        all_rels = self.env['amunet.quality.parameter.product.rel'].search([
            ('product_tmpl_id', 'in', all_tmpl_ids),
            ('parameter_code', 'in', all_param_codes)
        ])
        
        # 3. Organizar en un mapa de memoria: (tmpl_id, param_code) -> best_rel
        global_rel_map = {} # (tmpl_id, param_code) -> rel
        for rel in all_rels:
            if not rel.parameter_code: continue
            key = (rel.product_tmpl_id.id, rel.parameter_code)
            # Comparar para quedarnos con la "mejor" REL (más especificaciones)
            if key not in global_rel_map or len(rel.specification_config_ids) > len(global_rel_map[key].specification_config_ids):
                global_rel_map[key] = rel

        # 4. Asignar a cada registro
        for record in self:
            record_tmpl_ids = record.product_ids.mapped('product_tmpl_id').ids
            record_param_codes = record.parameter_ids.mapped('code')
            
            target_rel_ids = []
            for t_id in record_tmpl_ids:
                for p_code in record_param_codes:
                    if not p_code: continue
                    rel = global_rel_map.get((t_id, p_code))
                    if rel:
                        target_rel_ids.append(rel.id)
            
            # Usar set para evitar duplicados
            unique_ids = list(set(target_rel_ids))
            record.parameter_product_rel_ids = [(6, 0, unique_ids)]

    def apply_quality_points(self, picking):
        """
        Aplica puntos de control a un picking, creando QCs con parámetros.
        
        Returns:
            int: Número de QCs creados
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        QualityCheck = self.env['amunet.quality.check']
        TestLine = self.env['amunet.quality.test.line']
        
        # Buscar puntos activos para este tipo de operación
        points = self.search([
            ('active', '=', True),
            ('company_id', '=', picking.company_id.id),
            ('picking_type_ids', 'in', picking.picking_type_id.id)
        ])
        
        if not points:
            return 0
        
        qc_created = 0
        processed_keys = set()
        
        _logger.info(f"Processing {len(picking.move_line_ids)} move lines...")
        
        for move_line in picking.move_line_ids:
            product = move_line.product_id
            lot = move_line.lot_id
            
            _logger.info(f"  - Product: {product.name} (ID: {product.id})")
            _logger.info(f"    move_line.lot_id: {lot}")
            _logger.info(f"    move_line.lot_name: {getattr(move_line, 'lot_name', 'NO FIELD')}")
            
            # === NUEVA LÓGICA: Si lot_id está vacío pero lot_name existe, buscar o crear el lote ===
            if not lot and hasattr(move_line, 'lot_name') and move_line.lot_name:
                _logger.info(f"    Searching/creating lot {move_line.lot_name}...")
                lot = self.env['stock.lot'].search([
                    ('name', '=', move_line.lot_name),
                    ('product_id', '=', product.id),
                    ('company_id', '=', picking.company_id.id)
                ], limit=1)
                
                if not lot:
                    # Crear el lote con los datos disponibles en move_line
                    lot_vals = {
                        'name': move_line.lot_name,
                        'product_id': product.id,
                        'company_id': picking.company_id.id,
                    }
                    
                    # Agregar fecha de fabricación si está disponible
                    if hasattr(move_line, 'manufacturing_date') and move_line.manufacturing_date:
                        lot_vals['manufacturing_date'] = move_line.manufacturing_date
                    
                    # Agregar fechas de vencimiento/remoción si están disponibles
                    if hasattr(move_line, 'expiration_date') and move_line.expiration_date:
                        lot_vals['expiration_date'] = move_line.expiration_date
                    if hasattr(move_line, 'removal_date') and move_line.removal_date:
                        lot_vals['removal_date'] = move_line.removal_date
                    
                    # Agregar factory_lot_id si está disponible
                    if hasattr(move_line, 'factory_lot_id') and move_line.factory_lot_id:
                        lot_vals['factory_lot_id'] = move_line.factory_lot_id.id
                    
                    lot = self.env['stock.lot'].sudo().create(lot_vals)
                    _logger.info(f"    Created lot {lot.name} (ID: {lot.id})")
                else:
                    _logger.info(f"    Found existing lot {lot.name} (ID: {lot.id})")
                
                # Asignar el lote al move_line para que Odoo lo use en la validación
                move_line.lot_id = lot.id
            
            # Filtrar puntos aplicables a este producto
            applicable_points = points.filtered(lambda p: product in p.product_ids)
            
            _logger.info(f"    Applicable points for this product: {len(applicable_points)}")
            if applicable_points:
                _logger.info(f"    Point IDs: {applicable_points.ids}")
                for point in applicable_points:
                    _logger.info(f"      - Point: {point.name} covering products: {point.product_ids.mapped('name')}")
            
            if not applicable_points:
                _logger.info("    SKIPPED: No applicable points")
                continue
            
            # Evitar duplicados por producto/lote
            key = (product.id, lot.id if lot else 0)
            if key in processed_keys:
                continue
            processed_keys.add(key)
            
            qc_vals = {
                'picking_id': picking.id,
                'product_id': product.id,
                'lot_id': lot.id if lot else False,
            }
            
            # EXTRAER UOM DE MUESTREO
            # Prioridad 1: UoM de la línea de movimiento (move_line)
            if hasattr(move_line, 'product_uom_id') and move_line.product_uom_id:
                qc_vals['sampling_uom_id'] = move_line.product_uom_id.id
            # Prioridad 2: UoM del producto
            elif product.uom_id:
                qc_vals['sampling_uom_id'] = product.uom_id.id
            
            # EXTRAER FABRICANTE/PROVEEDOR
            if picking.partner_id:
                qc_vals['partner_id'] = picking.partner_id.id
            
            # EXTRAER FECHAS - Prioridad: lot > move_line > fallback
            # 1. Fecha de fabricación
            if lot and hasattr(lot, 'manufacturing_date') and lot.manufacturing_date:
                qc_vals['manufacturing_date'] = lot.manufacturing_date
            elif hasattr(move_line, 'manufacturing_date') and move_line.manufacturing_date:
                qc_vals['manufacturing_date'] = move_line.manufacturing_date
            
            # 2. Fecha de caducidad
            if lot and hasattr(lot, 'expiration_date') and lot.expiration_date:
                qc_vals['expiration_date'] = lot.expiration_date
            elif hasattr(move_line, 'expiration_date') and move_line.expiration_date:
                # Convertir datetime a date si es necesario
                exp_date = move_line.expiration_date
                if hasattr(exp_date, 'date'):
                    qc_vals['expiration_date'] = exp_date.date()
                else:
                    qc_vals['expiration_date'] = exp_date
            
            # 3. Fecha de remoción
            if lot and hasattr(lot, 'removal_date') and lot.removal_date:
                qc_vals['removal_date'] = lot.removal_date
            elif hasattr(move_line, 'removal_date') and move_line.removal_date:
                # Convertir datetime a date si es necesario
                rem_date = move_line.removal_date
                if hasattr(rem_date, 'date'):
                    qc_vals['removal_date'] = rem_date.date()
                else:
                    qc_vals['removal_date'] = rem_date
            
            # FALLBACK: Si aún no hay fecha de fabricación, usar scheduled_date o hoy
            if 'manufacturing_date' not in qc_vals or not qc_vals.get('manufacturing_date'):
                if picking.scheduled_date:
                    qc_vals['manufacturing_date'] = picking.scheduled_date.date() \
                        if hasattr(picking.scheduled_date, 'date') else picking.scheduled_date
                else:
                    qc_vals['manufacturing_date'] = fields.Date.today()
            
            # 5. CREAR QC CON TODOS LOS DATOS
            qc = QualityCheck.create(qc_vals)
            
            # Cargar parámetros desde todos los puntos aplicables
            for point in applicable_points:
                for param in point.parameter_ids:
                    # VERIFICACIÓN DE DUPLICADOS: No crear si el parámetro ya fue cargado (Epic-031/create)
                    existing_line = qc.test_line_ids.filtered(lambda l: l.parameter_id.id == param.id)
                    if existing_line:
                        _logger.debug(f"      - Parámetro {param.name} ya existe en QC {qc.name}, saltando.")
                        continue

                    # Buscar la configuración específica para este producto (por template)
                    param_rel = self.env['amunet.quality.parameter.product.rel'].search([
                        ('product_tmpl_id', '=', product.product_tmpl_id.id),
                        ('parameter_id', '=', param.id)
                    ], limit=1)

                    TestLine.create({
                        'check_id': qc.id,
                        'parameter_id': param.id,
                        'parameter_rel_id': param_rel.id if param_rel else False,
                        'name': param.name,
                        'code': param.code,
                    })
            
            qc_created += 1
        
        return qc_created
