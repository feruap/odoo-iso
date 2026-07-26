# -*- coding: utf-8 -*-

import math

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError


class AmunetWooLongProcess(models.Model):
    """Perfil auditable de proceso largo por hoja maestra.

    Vincula un producto final con su hoja maestra y la BOM larga que la
    produce, y calcula hojas/piezas potenciales. Todo es de solo lectura
    sobre inventario/BOM/lotes; cada resultado trae bandera calculable y
    razón. El inventario existente y la capacidad potencial se muestran
    siempre por separado.
    """

    _name = 'amunet.woo.long.process'
    _description = 'Perfil de proceso largo por hoja maestra'
    _inherit = ['mail.thread']
    _order = 'name, id'

    name = fields.Char(string='Nombre del perfil', required=True, tracking=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Compañía', required=True,
        default=lambda self: self.env.company, index=True)

    product_id = fields.Many2one(
        'product.product', string='Producto final', required=True,
        tracking=True, index=True)
    master_product_id = fields.Many2one(
        'product.product', string='Producto hoja maestra', required=True,
        tracking=True)
    master_uom_id = fields.Many2one(
        'uom.uom', string='UoM hoja maestra',
        related='master_product_id.uom_id', readonly=True)
    bom_id = fields.Many2one(
        'mrp.bom', string='BOM larga (produce la hoja maestra)', tracking=True,
        help='Lista de materiales que produce la hoja maestra.')

    equivalence_type = fields.Selection([
        ('pieces', 'Piezas por hoja'),
        ('cm', 'Centímetros utilizables por hoja + piezas por centímetro'),
    ], string='Tipo de equivalencia', default='pieces', required=True,
        tracking=True)
    pieces_per_sheet = fields.Float(
        string='Piezas por hoja', default=0.0, tracking=True)
    usable_cm_per_sheet = fields.Float(
        string='Centímetros utilizables por hoja', default=0.0, tracking=True)
    pieces_per_cm = fields.Float(
        string='Piezas por centímetro', default=0.0, tracking=True)

    yield_percent = fields.Float(
        string='Rendimiento esperado (%)', default=100.0, tracking=True)
    scrap_percent = fields.Float(
        string='Porcentaje de merma (%)', default=0.0, tracking=True)

    quality_release_required = fields.Boolean(
        string='Exige liberación de calidad', default=False, tracking=True,
        help='Si está activo, solo las cantidades de lotes liberados cuentan '
             'como disponibles.')
    source_location_id = fields.Many2one(
        'stock.location', string='Ubicación fuente',
        domain="[('usage', '=', 'internal')]", tracking=True,
        help='Opcional. Vacío = ubicación fuente del tipo de operación de la '
             'BOM larga.')
    notes = fields.Text(string='Notas')

    # Existencia de hoja maestra (inventario ya existente)
    master_qty_physical = fields.Float(
        string='Hojas físicas (valor)', compute='_compute_master_stock')
    master_qty_released = fields.Float(
        string='Hojas liberadas (valor)', compute='_compute_master_stock')
    master_stock_calculable = fields.Boolean(
        string='Existencia hoja calculable', compute='_compute_master_stock')
    master_stock_reason = fields.Char(
        string='Razón existencia hoja', compute='_compute_master_stock')
    master_physical_calculable = fields.Boolean(
        string='Hojas físicas calculables', compute='_compute_master_stock')
    master_physical_reason = fields.Char(
        string='Razón hojas físicas', compute='_compute_master_stock')
    master_released_calculable = fields.Boolean(
        string='Hojas liberadas calculables', compute='_compute_master_stock')
    master_released_reason = fields.Char(
        string='Razón hojas liberadas', compute='_compute_master_stock')
    master_physical_display = fields.Char(
        string='Hojas físicas', compute='_compute_master_stock')
    master_released_display = fields.Char(
        string='Hojas liberadas', compute='_compute_master_stock')

    # Capacidad potencial desde la BOM larga
    potential_sheets_from_bom = fields.Float(
        string='Hojas potenciales desde BOM larga (valor)',
        compute='_compute_potential_sheets')
    potential_sheets_calculable = fields.Boolean(
        string='Hojas potenciales calculables', compute='_compute_potential_sheets')
    potential_sheets_reason = fields.Char(
        string='Razón hojas potenciales', compute='_compute_potential_sheets')
    potential_sheets_display = fields.Char(
        string='Hojas potenciales desde BOM larga',
        compute='_compute_potential_sheets')

    # Piezas potenciales (separadas: inventario existente vs capacidad)
    pieces_from_physical = fields.Float(
        string='Piezas desde hojas físicas (valor)', compute='_compute_pieces')
    pieces_from_released = fields.Float(
        string='Piezas desde hojas liberadas (valor)',
        compute='_compute_pieces')
    pieces_from_bom = fields.Float(
        string='Piezas desde hojas potenciales (BOM larga)',
        compute='_compute_pieces')
    pieces_total_potential = fields.Float(
        string='Piezas potenciales totales (valor)',
        compute='_compute_pieces')
    pieces_calculable = fields.Boolean(
        string='Piezas calculables', compute='_compute_pieces')
    pieces_reason = fields.Char(
        string='Razón piezas', compute='_compute_pieces')
    pieces_from_physical_calculable = fields.Boolean(
        string='Piezas físicas calculables', compute='_compute_pieces')
    pieces_from_released_calculable = fields.Boolean(
        string='Piezas liberadas calculables', compute='_compute_pieces')
    pieces_from_bom_calculable = fields.Boolean(
        string='Piezas desde BOM calculables', compute='_compute_pieces')
    pieces_total_calculable = fields.Boolean(
        string='Piezas totales calculables', compute='_compute_pieces')
    pieces_from_physical_reason = fields.Char(
        string='Razón piezas físicas', compute='_compute_pieces')
    pieces_from_released_reason = fields.Char(
        string='Razón piezas liberadas', compute='_compute_pieces')
    pieces_from_bom_reason = fields.Char(
        string='Razón piezas desde BOM', compute='_compute_pieces')
    pieces_total_reason = fields.Char(
        string='Razón piezas totales', compute='_compute_pieces')
    pieces_from_physical_display = fields.Char(
        string='Piezas desde hojas físicas', compute='_compute_pieces')
    pieces_from_released_display = fields.Char(
        string='Piezas desde hojas liberadas', compute='_compute_pieces')
    pieces_from_bom_display = fields.Char(
        string='Piezas desde BOM larga', compute='_compute_pieces')
    pieces_total_display = fields.Char(
        string='Piezas potenciales totales', compute='_compute_pieces')

    _uniq_company_product = models.Constraint(
        'unique(company_id, product_id)',
        'Ya existe un perfil de proceso largo para este producto en la '
        'compañía.',
    )

    # --------------------------------------------------------------
    # Restricciones de rango
    # --------------------------------------------------------------

    @api.constrains('yield_percent')
    def _check_yield_percent(self):
        for rec in self:
            if not 0.0 <= rec.yield_percent <= 100.0:
                raise ValidationError(_(
                    'El rendimiento esperado debe estar entre 0 y 100 %% '
                    '(valor: %s).') % rec.yield_percent)

    @api.constrains('scrap_percent')
    def _check_scrap_percent(self):
        for rec in self:
            if not 0.0 <= rec.scrap_percent < 100.0:
                raise ValidationError(_(
                    'El porcentaje de merma debe ser mayor o igual a 0 y '
                    'menor a 100 %% '
                    '(valor: %s).') % rec.scrap_percent)

    @api.constrains('pieces_per_sheet', 'usable_cm_per_sheet', 'pieces_per_cm')
    def _check_equivalence_positive(self):
        for rec in self:
            if min(rec.pieces_per_sheet, rec.usable_cm_per_sheet,
                   rec.pieces_per_cm) < 0:
                raise ValidationError(_(
                    'Las equivalencias (piezas/cm por hoja) no pueden ser '
                    'negativas.'))

    @api.constrains('bom_id', 'master_product_id')
    def _check_bom_master(self):
        for rec in self:
            if rec.bom_id and rec.master_product_id:
                bom_product = rec.bom_id.product_id or \
                    rec.bom_id.product_tmpl_id.product_variant_id
                if bom_product and bom_product != rec.master_product_id:
                    raise ValidationError(_(
                        'La BOM larga debe producir la hoja maestra %s '
                        '(la BOM seleccionada produce %s).') % (
                        rec.master_product_id.display_name,
                        bom_product.display_name))

    @api.constrains(
        'company_id', 'product_id', 'master_product_id', 'bom_id')
    def _check_company_consistency(self):
        for rec in self:
            company_records = [
                rec.product_id, rec.master_product_id, rec.bom_id,
            ]
            if any(
                    item.company_id and item.company_id != rec.company_id
                    for item in company_records):
                raise ValidationError(_(
                    'Producto final, hoja maestra y BOM deben pertenecer a la '
                    'compañía del perfil (o ser compartidos).'))

    # --------------------------------------------------------------
    # Cálculos de solo lectura
    # --------------------------------------------------------------

    def _effective_location(self):
        """Ubicación fuente del perfil con fallback seguro a la de la BOM."""
        self.ensure_one()
        if self.source_location_id:
            return self.source_location_id
        picking_type = self.bom_id.picking_type_id
        if not picking_type:
            warehouse = self.env['stock.warehouse'].search(
                [('company_id', '=', self.company_id.id)], limit=1)
            picking_type = warehouse and warehouse.manu_type_id or False
        return picking_type and picking_type.default_location_src_id or False

    def _compute_master_stock(self):
        Quant = self.env['stock.quant']
        Lot = self.env['stock.lot']
        release_field = 'amunet_lot_release_state' in Lot._fields
        for rec in self:
            rec.master_qty_physical = 0.0
            rec.master_qty_released = 0.0
            rec.master_stock_calculable = False
            rec.master_stock_reason = False
            rec.master_physical_calculable = False
            rec.master_physical_reason = False
            rec.master_released_calculable = False
            rec.master_released_reason = False
            rec.master_physical_display = _('No calculable')
            rec.master_released_display = _('No calculable')
            if not rec.master_product_id:
                reason = _('No hay producto hoja maestra.')
                rec.master_stock_reason = reason
                rec.master_physical_reason = reason
                rec.master_released_reason = reason
                continue
            try:
                location = rec._effective_location()
            except AccessError:
                reason = _('Sin permiso para consultar ubicación o almacén.')
                rec.master_stock_reason = reason
                rec.master_physical_reason = reason
                rec.master_released_reason = reason
                continue
            domain = [
                ('product_id', '=', rec.master_product_id.id),
                ('company_id', '=', rec.company_id.id),
            ]
            if location:
                domain += [('location_id', 'child_of', location.id)]
            else:
                domain += [('location_id.usage', '=', 'internal')]
            try:
                quants = Quant.search(domain)
            except AccessError:
                reason = _(
                    'Sin permiso para consultar existencias de hoja maestra.')
                rec.master_stock_reason = reason
                rec.master_physical_reason = reason
                rec.master_released_reason = reason
                continue
            rec.master_qty_physical = sum(quants.mapped('quantity'))
            rec.master_physical_calculable = True
            rec.master_physical_display = '%g' % rec.master_qty_physical
            if not release_field:
                rec.master_released_reason = _(
                    'El campo regulatorio amunet_lot_release_state no existe '
                    'en stock.lot: la cantidad liberada es no calculable.')
            else:
                for quant in quants:
                    if quant.lot_id and \
                            quant.lot_id.amunet_lot_release_state == 'released':
                        rec.master_qty_released += quant.quantity
                rec.master_released_calculable = True
                rec.master_released_display = '%g' % rec.master_qty_released
            rec.master_stock_calculable = (
                rec.master_physical_calculable
                and (
                    not rec.quality_release_required
                    or rec.master_released_calculable
                )
            )
            if not rec.master_stock_calculable:
                rec.master_stock_reason = (
                    rec.master_released_reason
                    if rec.quality_release_required
                    else rec.master_physical_reason)

    def _compute_potential_sheets(self):
        Mapping = self.env['amunet.woo.product.mapping']
        for rec in self:
            rec.potential_sheets_from_bom = 0.0
            rec.potential_sheets_calculable = False
            rec.potential_sheets_reason = False
            rec.potential_sheets_display = _('No calculable')
            if not rec.master_product_id:
                rec.potential_sheets_reason = _('No hay producto hoja maestra.')
                continue
            if not rec.bom_id:
                rec.potential_sheets_reason = _(
                    'No hay BOM larga configurada para la hoja maestra.')
                continue
            qty, calculable, reason = Mapping._capacity_from_bom(
                rec.bom_id, rec.master_product_id, rec.company_id,
                location=rec.source_location_id or None)
            rec.potential_sheets_from_bom = qty
            rec.potential_sheets_calculable = calculable
            rec.potential_sheets_reason = reason
            rec.potential_sheets_display = (
                '%g' % qty if calculable else _('No calculable'))

    def _equivalence_factor(self):
        """Piezas brutas por hoja según el tipo de equivalencia.

        Regresa (factor, calculable, reason)."""
        self.ensure_one()
        if self.equivalence_type == 'pieces':
            if self.pieces_per_sheet <= 0:
                return 0.0, False, _(
                    'Equivalencia "piezas por hoja" sin valor válido (> 0).')
            return self.pieces_per_sheet, True, False
        if self.usable_cm_per_sheet <= 0 or self.pieces_per_cm <= 0:
            return 0.0, False, _(
                'Equivalencia por centímetros incompleta: se requieren '
                'centímetros utilizables por hoja y piezas por centímetro '
                'mayores a cero.')
        return self.usable_cm_per_sheet * self.pieces_per_cm, True, False

    def _pieces(self, sheets, factor):
        """Piezas enteras desde hojas aplicando rendimiento y merma."""
        adjusted = factor * (self.yield_percent / 100.0) * (
            1.0 - self.scrap_percent / 100.0)
        return math.floor(sheets * adjusted)

    def _compute_pieces(self):
        for rec in self:
            rec.pieces_from_physical = 0.0
            rec.pieces_from_released = 0.0
            rec.pieces_from_bom = 0.0
            rec.pieces_total_potential = 0.0
            rec.pieces_calculable = False
            rec.pieces_reason = False
            rec.pieces_from_physical_calculable = False
            rec.pieces_from_released_calculable = False
            rec.pieces_from_bom_calculable = False
            rec.pieces_total_calculable = False
            rec.pieces_from_physical_reason = False
            rec.pieces_from_released_reason = False
            rec.pieces_from_bom_reason = False
            rec.pieces_total_reason = False
            rec.pieces_from_physical_display = _('No calculable')
            rec.pieces_from_released_display = _('No calculable')
            rec.pieces_from_bom_display = _('No calculable')
            rec.pieces_total_display = _('No calculable')
            factor, ok, reason = rec._equivalence_factor()
            if not ok:
                rec.pieces_reason = reason
                rec.pieces_from_physical_reason = reason
                rec.pieces_from_released_reason = reason
                rec.pieces_from_bom_reason = reason
                rec.pieces_total_reason = reason
                continue
            if rec.master_physical_calculable:
                rec.pieces_from_physical = rec._pieces(
                    rec.master_qty_physical, factor)
                rec.pieces_from_physical_calculable = True
                rec.pieces_from_physical_display = (
                    '%g' % rec.pieces_from_physical)
            else:
                rec.pieces_from_physical_reason = (
                    rec.master_physical_reason
                    or _('Las hojas físicas no son calculables.'))
            if rec.master_released_calculable:
                rec.pieces_from_released = rec._pieces(
                    rec.master_qty_released, factor)
                rec.pieces_from_released_calculable = True
                rec.pieces_from_released_display = (
                    '%g' % rec.pieces_from_released)
            else:
                rec.pieces_from_released_reason = (
                    rec.master_released_reason
                    or _('Las hojas liberadas no son calculables.'))
            if rec.potential_sheets_calculable:
                rec.pieces_from_bom = rec._pieces(
                    rec.potential_sheets_from_bom, factor)
                rec.pieces_from_bom_calculable = True
                rec.pieces_from_bom_display = '%g' % rec.pieces_from_bom
            else:
                rec.pieces_from_bom_reason = (
                    rec.potential_sheets_reason
                    or _('Las hojas potenciales desde la BOM no son calculables.'))

            base_ok = (
                rec.master_released_calculable
                if rec.quality_release_required
                else rec.master_physical_calculable
            )
            if base_ok and rec.potential_sheets_calculable:
                base = (
                    rec.master_qty_released
                    if rec.quality_release_required
                    else rec.master_qty_physical
                )
                rec.pieces_total_potential = rec._pieces(
                    base + rec.potential_sheets_from_bom, factor)
                rec.pieces_total_calculable = True
                rec.pieces_total_display = '%g' % rec.pieces_total_potential
            else:
                reasons = []
                if not base_ok:
                    reasons.append(
                        rec.master_released_reason
                        if rec.quality_release_required
                        else rec.master_physical_reason)
                if not rec.potential_sheets_calculable:
                    reasons.append(rec.potential_sheets_reason)
                rec.pieces_total_reason = '; '.join(
                    reason for reason in reasons if reason
                ) or _('Las piezas totales no son calculables.')
            rec.pieces_calculable = rec.pieces_total_calculable
            rec.pieces_reason = rec.pieces_total_reason
