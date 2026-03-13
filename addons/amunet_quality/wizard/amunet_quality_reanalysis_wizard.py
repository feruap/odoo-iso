# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AmunetQualityReanalysisWizard(models.TransientModel):
    """
    Wizard para crear un reanálisis de Control de Calidad.

    T-029-15: Implementar funcionalidad de reanálisis

    Permite:
    - Especificar cantidad a muestrear para el reanálisis
    - Mantener trazabilidad con el análisis original
    - Transferir automáticamente stock para el nuevo muestreo
    """
    _name = 'amunet.quality.reanalysis.wizard'
    _description = 'Wizard de Reanálisis de Control de Calidad'

    # ========== Campos ==========

    quality_check_id = fields.Many2one(
        'amunet.quality.check',
        string='Control de calidad original',
        required=True,
        readonly=True
    )

    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        related='quality_check_id.product_id',
        readonly=True
    )

    lot_id = fields.Many2one(
        'stock.lot',
        string='Lote',
        related='quality_check_id.lot_id',
        readonly=True
    )

    original_analysis_number = fields.Char(
        string='No. Análisis original',
        related='quality_check_id.analysis_number',
        readonly=True
    )

    original_result = fields.Selection(
        related='quality_check_id.global_result',
        string='Resultado original',
        readonly=True
    )

    qty_available = fields.Float(
        string='Stock disponible',
        compute='_compute_qty_available',
        digits='Product Unit of Measure'
    )

    qty_reanalysis = fields.Float(
        string='Cantidad para reanálisis',
        digits='Product Unit of Measure',
        required=True,
        help='Cantidad a muestrear para el reanálisis'
    )

    reanalysis_uom_id = fields.Many2one(
        'uom.uom',
        string='Unidad de medida',
        help='Unidad de medida para la cantidad de reanálisis'
    )

    reason = fields.Text(
        string='Motivo del reanálisis',
        required=True,
        help='Explique brevemente por qué se requiere un reanálisis'
    )

    # ========== Computados ==========

    @api.depends('lot_id', 'product_id')
    def _compute_qty_available(self):
        """
        Calcula el stock disponible del lote únicamente en ubicaciones de
        Existencias (lot_stock_id de cada almacén y sus ubicaciones hijas),
        excluyendo ubicaciones de Control de Calidad u otras intermedias.
        """
        for record in self:
            if record.lot_id and record.product_id:
                stock_locations = self.env['stock.warehouse'].search([]).mapped('lot_stock_id')
                if stock_locations:
                    quants = self.env['stock.quant'].search([
                        ('lot_id', '=', record.lot_id.id),
                        ('product_id', '=', record.product_id.id),
                        ('location_id', 'child_of', stock_locations.ids),
                    ])
                    record.qty_available = sum(quants.mapped('quantity'))
                else:
                    record.qty_available = 0.0
            else:
                record.qty_available = 0.0

    # ========== Valores por defecto ==========

    @api.model
    def default_get(self, fields_list):
        """Establece valores por defecto desde el contexto"""
        res = super().default_get(fields_list)

        active_id = self.env.context.get('active_id')
        if active_id:
            check = self.env['amunet.quality.check'].browse(active_id)
            res.update({
                'quality_check_id': check.id,
                'qty_reanalysis': 0.0,
                'reanalysis_uom_id': check.sampling_uom_id.id if check.sampling_uom_id else check.product_id.uom_id.id,
            })

        return res

    # ========== Acciones ==========

    def action_create_reanalysis(self):
        """
        Crea el reanálisis con los parámetros especificados.

        Returns:
            dict: Acción para abrir el nuevo QC
        """
        self.ensure_one()

        # Validaciones
        if self.qty_reanalysis <= 0:
            raise ValidationError('La cantidad para reanálisis debe ser mayor a 0')

        if self.qty_reanalysis > self.qty_available:
            raise ValidationError(
                f'La cantidad ({self.qty_reanalysis}) excede el stock disponible '
                f'({self.qty_available})'
            )

        if not self.reason or len(self.reason.strip()) < 10:
            raise ValidationError('Debe especificar un motivo para el reanálisis (mínimo 10 caracteres)')

        original = self.quality_check_id

        # Crear nuevo QC
        new_check = original.copy({
            'parent_check_id': original.id,
            'analysis_type': 'reanalysis',
            'reanalysis_count': original.reanalysis_count + 1,
            'state': 'draft',
            'analysis_number': False,
            'info_reviewed': False,
            'sampling_confirmed': False,
            'sampling_move_id': False,
            'qty_sampling': self.qty_reanalysis,
            'sampling_uom_id': self.reanalysis_uom_id.id if self.reanalysis_uom_id else False,
            'qty_analyzed': 0,
            'user_realized_id': False,
            'user_verified_id': False,
            'user_authorized_id': False,
            'reviewed_by_id': False,
            'reviewed_date': False,
            'sampling_date': False,
            'analysis_date': False,
            # Epic-032: Copiar información adicional del análisis original
            'additional_info_avg_length': original.additional_info_avg_length,
            'additional_info_cv_percent': original.additional_info_cv_percent,
            'additional_info_observations': original.additional_info_observations,
        })

        # Limpiar resultados
        new_check.test_line_ids.write({
            'result_numeric': 0,
            'result_selection': False,
        })

        # Registrar en el original
        original.message_post(
            body=f'Se creó reanálisis: {new_check.name}<br/>'
                 f'Cantidad: {self.qty_reanalysis} {self.reanalysis_uom_id.name if self.reanalysis_uom_id else ""}<br/>'
                 f'Motivo: {self.reason}',
            message_type='notification'
        )

        # Registrar en el nuevo
        new_check.message_post(
            body=f'Reanálisis creado desde: {original.name} ({original.analysis_number})<br/>'
                 f'Motivo: {self.reason}',
            message_type='notification'
        )

        # Si el wizard fue abierto desde inventario (stock.lot):
        #   - Confirmar el muestreo automáticamente (genera movimiento Existencias → Control QC)
        #   - Regresar al lote (el usuario de inventario no debe ver el QC)
        origin_model = self.env.context.get('origin_model')
        if origin_model == 'stock.lot':
            # Confirmar muestreo: crea y valida el movimiento de stock automáticamente
            new_check.action_confirm_sampling()

            lot_id = self.env.context.get('origin_lot_id')
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.lot',
                'res_id': lot_id,
                'view_mode': 'form',
                'target': 'current',
            }

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'amunet.quality.check',
            'res_id': new_check.id,
            'view_mode': 'form',
            'target': 'current',
        }










