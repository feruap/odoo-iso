# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    """
    Extensión de stock.picking para Control de Calidad Amunet.
    """
    _inherit = 'stock.picking'

    amunet_qc_ids = fields.One2many(
        'amunet.quality.check', 
        'picking_id', 
        string='Controles de Calidad'
    )
    
    amunet_qc_count = fields.Integer(
        string='Conteo QC', 
        compute='_compute_amunet_qc_count'
    )
    
    amunet_disposition_qc_id = fields.Many2one(
        'amunet.quality.check',
        string='QC de Disposición',
        help='QC que generó este movimiento de disposición',
        ondelete='set null'
    )
    
    has_quality_points = fields.Boolean(
        string='Tiene puntos de calidad',
        compute='_compute_has_quality_points',
        help='Indica si algún producto del picking tiene puntos de calidad configurados'
    )

    @api.depends('move_line_ids', 'move_line_ids.product_id', 'picking_type_id')
    def _compute_has_quality_points(self):
        """Verifica si hay productos con quality points configurados para este picking"""
        for record in self:
            has_points = False
            if record.move_line_ids and record.picking_type_id:
                # Buscar puntos de calidad para este tipo de operación
                points = self.env['amunet.quality.point'].search([
                    ('active', '=', True),
                    ('company_id', '=', record.company_id.id),
                    ('picking_type_ids', 'in', record.picking_type_id.id)
                ])
                
                if points:
                    # Verificar si algún producto del picking tiene puntos configurados
                    product_ids = record.move_line_ids.mapped('product_id')
                    for point in points:
                        if any(product in point.product_ids for product in product_ids):
                            has_points = True
                            break
            
            record.has_quality_points = has_points

    @api.depends('amunet_qc_ids')
    def _compute_amunet_qc_count(self):
        for record in self:
            record.amunet_qc_count = len(record.amunet_qc_ids)

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create para sanitizar referencias nativas inválidas ANTES de que
        Odoo intente escribir en la base de datos y cause crash.
        """
        # 1. CLEAN VALS AGGRESSIVELY
        for vals in vals_list:
            # Remove any explicit reference to quality.check fields
            for forbidden in ['quality_check_id', 'check_ids']:
                if forbidden in vals:
                    _logger.warning(f"Removing forbidden field {forbidden} from vals")
                    vals.pop(forbidden)

            # 2. CLEAN MOVE_IDS IN VALS
            if 'move_ids' in vals and vals['move_ids']:
                for move_tuple in vals['move_ids']:
                    # (0, 0, {vals})
                    if len(move_tuple) == 3 and isinstance(move_tuple[2], dict):
                        move_vals = move_tuple[2]
                        if 'quality_check_id' in move_vals:
                             _logger.warning("Removing quality_check_id from move_vals")
                             move_vals.pop('quality_check_id')

        # 3. SELECTIVE CONTEXT CLEANING
        # Solo eliminamos lo que viene específicamente de los wizards de calidad nativos
        # para evitar fallos de persistencia, pero mantenemos lo estándar de Odoo.
        clean_context = dict(self.env.context)
        keys_to_remove = [
            'default_check_ids', 
            'default_quality_check_id',
        ]
        
        # Eliminar cualquier key que contenga 'check_ids'
        keys_to_pop = [k for k in clean_context.keys() if 'check_ids' in k]
        for k in keys_to_pop:
            clean_context.pop(k, None)
            
        for key in keys_to_remove:
            clean_context.pop(key, None)
            
        _logger.info(f"Stock Picking Create: Sanitized context for {len(vals_list)} records")

        return super(StockPicking, self.with_context(clean_context)).create(vals_list)

    def action_confirm(self):
        """
        Override para confirmar picking.
        
        NOTA: Los QCs se crean en button_validate() en lugar de aquí,
        para asegurar que los lotes ya estén asignados en las move_lines.
        """
        res = super(StockPicking, self).action_confirm()
        # Los QCs se generan en button_validate() para tener acceso a los lotes.
        return res

    def button_validate(self):
        """
        Override original para integración completa de Calidad Amunet.
        0. SUPRESIÓN TEMPRANA: Aprueba checks nativos ANTES de que el wizard se dispare
        1. CREACIÓN DE QCS: Generar QCs ANTES de validación (con lotes disponibles).
        2. VALIDACIÓN: Impide validar si hay QCs Amunet pendientes/fallidos.
        """
        # 0. SUPRESIÓN TEMPRANA: Auto-aprobar checks nativos ANTES del wizard
        for picking in self:
            if hasattr(picking, 'check_ids'):
                try:
                    native_checks = picking.check_ids.exists()
                    if native_checks:
                        _logger.info(f"EARLY: Auto-passing {len(native_checks)} native quality checks for picking {picking.name}")
                        for check in native_checks:
                            try:
                                if hasattr(check, 'do_pass'):
                                    check.do_pass()
                                elif hasattr(check, 'action_pass'):
                                    check.action_pass()
                                elif hasattr(check, 'quality_state'):
                                    check.write({'quality_state': 'pass'})
                                elif hasattr(check, 'state'):
                                    check.write({'state': 'pass'})
                            except Exception as e:
                                _logger.warning(f"Failed to pass check {check.id}: {e}")
                except Exception as e:
                    _logger.warning(f"EARLY suppression error: {e}")
        
        # 1. CREACIÓN DE QCS: Generar QCs Amunet si no existen
        for picking in self:
            if picking.origin and picking.origin.startswith('Muestreo QC'):
                continue
            
            if not picking.amunet_qc_ids:
                qc_created = self.env['amunet.quality.point'].apply_quality_points(picking)
                if qc_created:
                    _logger.info(f"Created {qc_created} quality check(s) for picking {picking.name}")

        # 2. ENFORCEMENT: (DESHABILITADO por requerimiento del usuario)
        # Se permite validar aunque existan controles de calidad pendientes.
        # Los controles se crean automáticamente arriba, pero no bloquean el ingreso.
        # for picking in self:
        #     pending_qcs = picking.amunet_qc_ids.filtered(lambda qc: qc.state not in ('done', 'pass'))
        #     
        #     if pending_qcs:
        #         raise ValidationError(f"No puede validar la transferencia porque hay controles de calidad pendientes:\n" + 
        #                             "\n".join([f"- {qc.product_id.name}" for qc in pending_qcs]))
        
        # 3. LIMPIEZA: Asegurar que no haya referencias fantasma
        for picking in self:
            if hasattr(picking, 'quality_check_id'):
                try:
                    if not picking.quality_check_id.exists():
                        picking.quality_check_id = False
                except Exception:
                    picking.quality_check_id = False
            
            if hasattr(picking, 'move_ids'):
                for move in picking.move_ids:
                    if hasattr(move, 'quality_check_id'):
                        try:
                            if not move.quality_check_id.exists():
                                move.quality_check_id = False
                        except Exception:
                            move.quality_check_id = False
                         
        return super(StockPicking, self).button_validate()

    def action_view_quality_checks(self):
        """Abre los controles de calidad del picking. Si no existen, los crea primero."""
        self.ensure_one()
        
        # Si no hay QCs Amunet, crearlos automáticamente
        if not self.amunet_qc_ids:
            qc_created = self.env['amunet.quality.point'].apply_quality_points(self)
            if qc_created:
                _logger.info(f"Created {qc_created} quality check(s) when opening QC view for picking {self.name}")
            else:
                # No se crearon QCs, probablemente no hay quality points configurados
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Sin controles de calidad',
                        'message': 'No hay puntos de control de calidad configurados para este producto.',
                        'type': 'warning',
                        'sticky': False,
                    }
                }

        # Si solo hay 1 QC, abrir directamente el formulario
        if self.amunet_qc_count == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'amunet.quality.check',
                'res_id': self.amunet_qc_ids[0].id,
                'view_mode': 'form',
                'target': 'current',
            }

        # Si hay múltiples QCs, mostrar la lista
        return {
            'type': 'ir.actions.act_window',
            'name': 'Controles de Calidad',
            'res_model': 'amunet.quality.check',
            'view_mode': 'list,form',
            'domain': [('picking_id', '=', self.id)],
        }
