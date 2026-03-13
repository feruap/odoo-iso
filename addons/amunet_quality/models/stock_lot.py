# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class StockLot(models.Model):
    """
    Extensión de stock.lot para integrar reanálisis desde Inventario.

    Permite a los usuarios de inventario visualizar los controles de calidad
    asociados a un lote y solicitar un reanálisis directamente desde el
    formulario de lote, sin necesidad de acceder al módulo de Calidad.
    """
    _inherit = 'stock.lot'

    # ========== Campos relacionales ==========

    quality_check_ids = fields.One2many(
        'amunet.quality.check',
        'lot_id',
        string='Controles de calidad',
    )

    quality_check_count = fields.Integer(
        string='Controles QC',
        compute='_compute_quality_check_count',
    )

    last_quality_check_id = fields.Many2one(
        'amunet.quality.check',
        string='Último control de calidad',
        compute='_compute_last_quality_check_id',
    )

    can_request_reanalysis = fields.Boolean(
        string='Puede solicitar reanálisis',
        compute='_compute_can_request_reanalysis',
    )

    # ========== Computados ==========

    @api.depends('quality_check_ids')
    def _compute_quality_check_count(self):
        for lot in self:
            lot.quality_check_count = len(lot.quality_check_ids)

    @api.depends('quality_check_ids', 'quality_check_ids.state')
    def _compute_last_quality_check_id(self):
        """Retorna el QC completado más reciente del lote (done o pending)."""
        for lot in self:
            done_checks = lot.quality_check_ids.filtered(
                lambda c: c.state in ('done', 'pending')
            ).sorted('id', reverse=True)
            lot.last_quality_check_id = done_checks[0] if done_checks else False

    @api.depends('last_quality_check_id')
    def _compute_can_request_reanalysis(self):
        for lot in self:
            lot.can_request_reanalysis = bool(lot.last_quality_check_id)

    # ========== Acciones ==========

    def action_view_quality_checks(self):
        """Abre la lista de controles de calidad asociados a este lote."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Controles de calidad — {self.name}',
            'res_model': 'amunet.quality.check',
            'view_mode': 'list,form',
            'domain': [('lot_id', '=', self.id)],
            'context': {'default_lot_id': self.id},
        }

    def action_request_reanalysis(self):
        """
        Abre el wizard de reanálisis desde Inventario.

        Busca el control de calidad completado más reciente del lote y abre
        el wizard preconfigurado con ese análisis. Si no existe ningún análisis
        completado, muestra un mensaje de error al usuario.
        """
        self.ensure_one()
        if not self.last_quality_check_id:
            raise UserError(
                'No existe ningún análisis de calidad completado para el lote "%s".\n\n'
                'Solo es posible solicitar un reanálisis de lotes que ya pasaron '
                'por Control de Calidad (estado: En revisión o Finalizado).' % self.name
            )
        return {
            'type': 'ir.actions.act_window',
            'name': 'Solicitar reanálisis',
            'res_model': 'amunet.quality.reanalysis.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.last_quality_check_id.id,
                'active_model': 'amunet.quality.check',
                'origin_model': 'stock.lot',
                'origin_lot_id': self.id,
            },
        }
