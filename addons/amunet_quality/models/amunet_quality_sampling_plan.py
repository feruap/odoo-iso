# -*- coding: utf-8 -*-

import math

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AmunetQualitySamplingPlan(models.Model):
    _name = 'amunet.quality.sampling.plan'
    _description = 'Plan de Muestreo de Calidad'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, lot_min, id'

    name = fields.Char(string='Nombre', required=True, tracking=True)
    code = fields.Char(string='Codigo', required=True, tracking=True, index=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)

    family = fields.Selection([
        ('equipment_resale', 'Equipo comprado / reventa'),
        ('uncut_sheet', 'Hoja impregnada / hoja maestra'),
        ('cassette', 'Cassette / cartucho'),
        ('biological_raw', 'Materia prima biologica critica'),
        ('buffer_solution', 'Buffer / solucion / reactivo liquido'),
        ('finished_rdt', 'Producto terminado RDT'),
        ('packaging', 'Empaque / material impreso'),
        ('default', 'Generico'),
    ], string='Familia', required=True, default='default', tracking=True)

    stage = fields.Selection([
        ('receipt', 'Recepcion'),
        ('in_process', 'Proceso'),
        ('final_release', 'Liberacion final'),
    ], string='Etapa', required=True, default='receipt', tracking=True)

    product_ids = fields.Many2many(
        'product.product',
        'amunet_quality_sampling_plan_product_rel',
        'plan_id',
        'product_id',
        string='Productos especificos',
    )
    categ_ids = fields.Many2many(
        'product.category',
        'amunet_quality_sampling_plan_category_rel',
        'plan_id',
        'categ_id',
        string='Categorias aplicables',
    )

    lot_min = fields.Float(string='Lote desde', default=0.0, required=True)
    lot_max = fields.Float(
        string='Lote hasta',
        default=0.0,
        help='0 significa sin limite superior.',
    )

    method = fields.Selection([
        ('full', '100%'),
        ('fixed', 'Cantidad fija'),
        ('percent', 'Porcentaje'),
        ('aql_table', 'Tabla AQL/ISO 2859-1 base'),
        ('technical_minimum', 'Minimo tecnico'),
    ], string='Metodo', required=True, default='aql_table', tracking=True)

    fixed_qty = fields.Float(string='Cantidad fija', default=0.0)
    percent = fields.Float(string='Porcentaje', default=0.0)
    min_qty = fields.Float(string='Minimo', default=0.0)
    max_qty = fields.Float(string='Maximo', default=0.0)

    critical_accept = fields.Integer(string='Critico acepta', default=0)
    critical_reject = fields.Integer(string='Critico rechaza', default=1)
    major_accept = fields.Integer(string='Mayor acepta', default=0)
    major_reject = fields.Integer(string='Mayor rechaza', default=1)
    minor_accept = fields.Integer(string='Menor acepta', default=0)
    minor_reject = fields.Integer(string='Menor rechaza', default=1)

    functional_sample_note = fields.Text(
        string='Nota de muestra funcional',
        help='Submuestra funcional o destructiva que complementa la muestra visual/documental.',
    )
    regulatory_basis = fields.Text(
        string='Justificacion',
        help='Justificacion estadistica, tecnica o regulatoria del plan.',
    )
    procedure_id = fields.Many2one('amunet.quality.procedure', string='Procedimiento')

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'El codigo del plan de muestreo debe ser unico.'),
    ]

    @api.constrains('lot_min', 'lot_max', 'percent', 'fixed_qty', 'min_qty', 'max_qty')
    def _check_numeric_values(self):
        for plan in self:
            if plan.lot_min < 0 or plan.lot_max < 0:
                raise ValidationError(_('Los rangos de lote no pueden ser negativos.'))
            if plan.lot_max and plan.lot_max < plan.lot_min:
                raise ValidationError(_('El lote hasta no puede ser menor al lote desde.'))
            if plan.percent < 0 or plan.percent > 100:
                raise ValidationError(_('El porcentaje debe estar entre 0 y 100.'))
            if plan.fixed_qty < 0 or plan.min_qty < 0 or plan.max_qty < 0:
                raise ValidationError(_('Las cantidades de muestra no pueden ser negativas.'))
            if plan.max_qty and plan.min_qty and plan.max_qty < plan.min_qty:
                raise ValidationError(_('El maximo no puede ser menor al minimo.'))

    def compute_sample_qty(self, lot_qty):
        self.ensure_one()
        lot_qty = lot_qty or 0.0
        if lot_qty <= 0:
            return 0.0

        if self.method == 'full':
            qty = lot_qty
        elif self.method == 'fixed':
            qty = self.fixed_qty
        elif self.method == 'percent':
            qty = math.ceil(lot_qty * (self.percent or 0.0) / 100.0)
        elif self.method == 'technical_minimum':
            qty = self.fixed_qty or self.min_qty or 1.0
        else:
            qty = self._aql_level_ii_sample_qty(lot_qty)

        if self.min_qty:
            qty = max(qty, self.min_qty)
        if self.max_qty:
            qty = min(qty, self.max_qty)
        return min(qty, lot_qty)

    @api.model
    def _aql_level_ii_sample_qty(self, lot_qty):
        """Base operational table for ISO 2859-1/ANSI Z1.4 general level II."""
        ranges = [
            (8, 2),
            (15, 3),
            (25, 5),
            (50, 8),
            (90, 13),
            (150, 20),
            (280, 32),
            (500, 50),
            (1200, 80),
            (3200, 125),
            (10000, 200),
            (35000, 315),
            (150000, 500),
            (500000, 800),
        ]
        for upper, sample in ranges:
            if lot_qty <= upper:
                return min(sample, lot_qty)
        return min(1250, lot_qty)

    @api.model
    def infer_stage_for_check(self, check):
        picking = check.picking_id
        if picking and picking.picking_type_id:
            code = picking.picking_type_id.code
            if code == 'incoming':
                return 'receipt'
            if code == 'internal':
                return 'in_process'
        product = check.product_id
        categ_name = product.categ_id.complete_name if product and product.categ_id else ''
        if 'Producto terminado' in categ_name:
            return 'final_release'
        return 'receipt'

    @api.model
    def infer_family_for_product(self, product):
        if not product:
            return 'default'
        tmpl = product.product_tmpl_id
        code = (product.default_code or '').upper()
        name = (product.display_name or '').lower()
        categ = (product.categ_id.complete_name or '').lower() if product.categ_id else ''
        tag_names = ' '.join(tmpl.product_tag_ids.mapped('name')).lower() if 'product_tag_ids' in tmpl._fields else ''

        if 'equipo' in categ or 'termobloque' in name or 'thermoblock' in name:
            return 'equipment_resale'
        if code.startswith(('SPHMC', 'SPHMT')) or 'hoja maestra' in name or 'uncut' in name:
            return 'uncut_sheet'
        if code.startswith(('MPCAR', 'MPCAC')) or 'cartucho' in name or 'cassette' in name or 'casete' in name:
            return 'cassette'
        if 'anticuerpo' in name or 'monoclonal' in name or 'policlonal' in name:
            return 'biological_raw'
        if 'solucion' in categ or 'soluciones' in categ or 'buffer' in name or 'reactivo liquido' in name:
            return 'buffer_solution'
        if 'producto terminado' in categ and ('prueba' in name or 'rdt' in tag_names or 'inmunologica' in tag_names):
            return 'finished_rdt'
        if 'material impreso' in categ or 'empaque' in categ or 'caja' in name or 'bolsa' in name or 'etiqueta' in name:
            return 'packaging'
        return 'default'

    @api.model
    def find_applicable_plan(self, product, lot_qty, stage=False):
        if not product:
            return self.browse()
        family = self.infer_family_for_product(product)
        stage = stage or 'receipt'
        lot_qty = lot_qty or 0.0
        plans = self.search([
            ('active', '=', True),
            ('stage', '=', stage),
            ('family', 'in', [family, 'default']),
            ('lot_min', '<=', lot_qty),
            '|',
            ('lot_max', '=', 0.0),
            ('lot_max', '>=', lot_qty),
        ])
        for plan in plans:
            if plan.product_ids and product not in plan.product_ids:
                continue
            if plan.categ_ids and product.categ_id not in plan.categ_ids:
                continue
            return plan
        return self.browse()

    def action_view_procedure(self):
        self.ensure_one()
        if not self.procedure_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'amunet.quality.procedure',
            'res_id': self.procedure_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
