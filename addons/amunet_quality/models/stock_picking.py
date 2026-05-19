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
            # Evitar recursividad: si el picking viene de una liberación o muestreo QC, no crear más QCs
            if picking.origin and any(picking.origin.startswith(s) for s in ['Muestreo QC', 'Liberación QC', 'Liberacion QC']):
                continue
            
            if not picking.amunet_qc_ids:
                qc_created = self.env['amunet.quality.point'].sudo().apply_quality_points(picking)
                if qc_created:
                    _logger.info(f"Created {qc_created} quality check(s) for picking {picking.name}")
                    
            # 1.5 CAPTURAR DESTINOS ORIGINALES antes de sobreescribir a Cuarentena
            if picking.amunet_qc_ids:
                qc_location = picking.amunet_qc_ids[0]._get_quality_control_location()
                if qc_location and picking.location_dest_id != qc_location:
                    DestLine = self.env['amunet.quality.check.destination'].sudo()
                    for qc in picking.amunet_qc_ids:
                        if not qc.destination_line_ids:
                            product_moves = picking.move_ids.filtered(
                                lambda m: m.product_id == qc.product_id
                                and m.state not in ('done', 'cancel')
                            )
                            qc_lot_name = qc.lot_id.name if qc.lot_id else qc.lot_name
                            
                            # Recorrer lineas exactas de movimiento para respetar multimples destinos por producto
                            for move in product_moves:
                                target_lines = move.move_line_ids
                                if qc_lot_name:
                                    target_lines = target_lines.filtered(
                                        lambda ml: (ml.lot_id.name if ml.lot_id else ml.lot_name) == qc_lot_name
                                    )
                                
                                for ml in target_lines:
                                    qty = getattr(ml, 'quantity', getattr(ml, 'qty_done', 0.0))
                                    if qty > 0:
                                        DestLine.create({
                                            'check_id': qc.id,
                                            'location_dest_id': ml.location_dest_id.id,
                                            'quantity': qty,
                                        })
                            _logger.info(
                                f"CAPTURA DESTINOS: QC {qc.name} → "
                                f"{len(qc.destination_line_ids)} destinos guardados"
                            )

                    # Ahora sobreescribir todo a Cuarentena
                    _logger.info(f"REDIRECCION: Forzando destino {qc_location.name} para {picking.name}")
                    picking.location_dest_id = qc_location
                    for move in picking.move_ids:
                        if move.state not in ('done', 'cancel'):
                            move.location_dest_id = qc_location
                            for ml in move.move_line_ids:
                                ml.location_dest_id = qc_location

        # 2. ENFORCEMENT: (DESHABILITADO por requerimiento del usuario)

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

        res = super(StockPicking, self).button_validate()

        self.env.invalidate_all()

        # 4. POST-VALIDATION: Cancelar pickings downstream y capturar qty_received.
        for picking in self:
            if not picking.amunet_qc_ids:
                continue
            for move in picking.move_ids:
                if move.state != 'done':
                    continue
                qc_for_product = picking.amunet_qc_ids.filtered(
                    lambda q: q.product_id == move.product_id
                )
                if not qc_for_product:
                    continue
                next_picking = move.move_dest_ids.mapped('picking_id')[:1]
                # original_dest_location_id legacy: usar primer destino de destination_line_ids
                for qc in qc_for_product:
                    if qc.destination_line_ids and not qc.original_dest_location_id:
                        qc.original_dest_location_id = qc.destination_line_ids[0].location_dest_id.id
                    elif not qc.original_dest_location_id:
                        final_location_id = move.location_dest_id.id
                        curr_move = move
                        while curr_move.move_dest_ids:
                            curr_move = curr_move.move_dest_ids[0]
                            final_location_id = curr_move.location_dest_id.id
                        qc.original_dest_location_id = final_location_id

                    if next_picking and not qc.pending_disposition_picking_id:
                        qc.pending_disposition_picking_id = next_picking.id
                    # Cancelar pickings downstream
                    to_cancel = self.env['stock.picking']
                    if qc.pending_disposition_picking_id and \
                       qc.pending_disposition_picking_id.state not in ('done', 'cancel'):
                        to_cancel |= qc.pending_disposition_picking_id
                    if qc.pending_disposition_picking_id:
                        downstream = qc.pending_disposition_picking_id.move_ids.mapped(
                            'move_dest_ids.picking_id'
                        ).filtered(lambda p: p.state not in ('done', 'cancel'))
                        to_cancel |= downstream
                    for p in to_cancel:
                        try:
                            p.action_cancel()
                            _logger.info(f"BLOQUEO: Cancelado {p.name} (QC: {qc.name})")
                        except Exception as e:
                            _logger.warning(f"Error cancelando {p.name}: {e}")

        # 5. Asignar validador y registrar qty_received
        for picking in self:
            if picking.amunet_disposition_qc_id:
                continue
            if picking.amunet_qc_ids:
                picking.amunet_qc_ids.sudo().write({
                    'inventory_validator_id': self.env.user.id
                })
                for qc in picking.amunet_qc_ids:
                    if not qc.original_qty_received:
                        if qc.destination_line_ids:
                            qty_received = sum(qc.destination_line_ids.mapped('quantity'))
                        else:
                            qty_received = sum(picking.move_line_ids.filtered(
                                lambda ml: ml.product_id == qc.product_id and ml.state == 'done'
                            ).mapped(lambda ml: ml.quantity if hasattr(ml, 'quantity') else (ml.qty_done if hasattr(ml, 'qty_done') else 0.0)))
                        if qty_received > 0:
                            try:
                                qc.sudo().write({'original_qty_received': qty_received})
                                _logger.info(f"Guardada cantidad original recibida {qty_received} para QC {qc.name}")
                            except Exception as e:
                                _logger.error(f"Error al guardar cantidad recibida para QC {qc.name}: {str(e)}")


        # =====================================================================
        # HOOK: Recepción final de QC aprobado
        # Detecta si este picking es la recepción de ingreso final generada por
        # _create_final_reception_picking() y cierra el QC correspondiente.
        # =====================================================================
        for picking in self:
            qc = picking.amunet_disposition_qc_id
            if qc and qc.state == 'awaiting_reception':
                try:
                    # Calcular qty real validada — filtro estricto por producto Y lote
                    qty_done = sum(
                        ml.quantity
                        for ml in picking.move_line_ids
                        if ml.product_id == qc.product_id
                        and (not qc.lot_id or ml.lot_id == qc.lot_id)
                    )

                    # Validar límites de negocio
                    from odoo.exceptions import UserError as StockUserError
                    if qty_done < 0:
                        raise StockUserError("La cantidad recibida no puede ser negativa.")

                    # Calcular cantidad esperada por Calidad
                    qty_total = qc.original_qty_received or qc.lot_qty_available
                    qty_expected = max(0.0,
                        qty_total - (qc.qty_sampling or 0.0) + (qc.qty_to_return or 0.0)
                    )
                    if qty_expected > 0 and qty_done > qty_expected:
                        raise StockUserError(
                            f"No puede recibir más cantidad ({qty_done:.2f}) "
                            f"de la que Calidad liberó ({qty_expected:.2f})."
                        )

                    # Cerrar el QC y registrar la confirmación
                    qc.sudo()._finalize_after_reception(qty_done)
                    _logger.info(
                        f"QC {qc.name} cerrado tras validación de recepción final "
                        f"por {self.env.user.name}. qty_done={qty_done}"
                    )
                except Exception as e:
                    _logger.error(f"Error en hook recepción final para QC {qc.name}: {str(e)}")
                    raise

        return res


    def action_view_quality_checks(self):
        """Abre los controles de calidad del picking. Si no existen, los crea primero."""
        self.ensure_one()
        
        # Si no hay QCs Amunet, crearlos automáticamente
        if not self.amunet_qc_ids:
            qc_created = self.env['amunet.quality.point'].sudo().apply_quality_points(self)
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
