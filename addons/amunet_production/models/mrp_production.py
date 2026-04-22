# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # Campos requeridos para Módulo de Soluciones
    quality_ph_initial = fields.Float(string='pH Inicial Objetivo', compute='_compute_quality_params', store=True, readonly=False)
    quality_ph_final = fields.Float(string='pH Final Obtenido')
    solution_lot_id = fields.Char(string='Lote de Solución', copy=False, help="Lote asignado a la solución final (interno)")
    
    solution_expiration_date = fields.Datetime(string='Fecha de Caducidad (Calendario)', compute='_compute_quality_params', store=True, readonly=False)
    amunet_expiration_text = fields.Char(string='Caducidad (Texto)', compute='_compute_quality_params', store=True, readonly=False)
    
    # Checklist Operativa (Actividades de Fabricación)
    amunet_check_history_log = fields.Boolean(string='Registro en Bitácoras', tracking=True)
    amunet_check_calculations = fields.Boolean(string='Cálculos Realizados', tracking=True)
    amunet_check_dilution = fields.Boolean(string='Dilución Realizada', tracking=True)
    amunet_check_aforar = fields.Boolean(string='Aforado Correcto', tracking=True)

    # Configuración arrastrada desde la plantilla
    amunet_sys_req_history = fields.Boolean(related='product_id.amunet_req_history_log')
    amunet_sys_req_calc = fields.Boolean(related='product_id.amunet_req_calculations')
    amunet_sys_weighing_range = fields.Char(string='Rango de Pesaje Operativo', compute='_compute_quality_params', store=True, readonly=False)
    amunet_sys_req_dilution = fields.Boolean(related='product_id.amunet_req_dilution')
    amunet_sys_ph_range = fields.Char(related='product_id.amunet_ph_adj_range_text')
    amunet_sys_req_aforar = fields.Boolean(related='product_id.amunet_req_aforar')
    
    # Campo lógico bidireccional hacia la plantilla del producto nativa (qc_required)
    amunet_sys_req_qc = fields.Boolean(
        string='Requiere Análisis C.C',
        related='product_id.qc_required', readonly=False, tracking=True,
        help="Permite anular o activar el pase por laboratorio bilateralmente."
    )
    
    quality_analysis_status = fields.Selection([
        ('none', 'No Requerido'),
        ('to_request', 'Pendiente de Solicitar'),
        ('requested', 'Análisis Solicitado'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado')
    ], string='Integración de Calidad', default='none', tracking=True, compute='_compute_quality_params', store=True, readonly=False)

    amunet_all_ingredients_valid = fields.Boolean(
        compute='_compute_all_ingredients_valid',
        string='Todos los ingredientes validos'
    )

    amunet_product_categ_id = fields.Many2one(
        'product.category',
        string='Categoria',
        compute='_compute_product_categ',
        store=False,
    )

    # Ocultar botones nativos de produccion (Produce / Produce All)
    show_produce = fields.Boolean(compute='_compute_show_produce_amunet', store=False)
    show_produce_all = fields.Boolean(compute='_compute_show_produce_amunet', store=False)

    def _compute_show_produce_amunet(self):
        for rec in self:
            rec.show_produce = False
            rec.show_produce_all = False

    @api.depends('product_id')
    def _compute_product_categ(self):
        for rec in self:
            rec.amunet_product_categ_id = rec.product_id.categ_id if rec.product_id else False

    @api.depends('product_id')
    def _compute_quality_params(self):
        for rec in self:
            if not rec.product_id:
                rec.quality_ph_initial = False
                rec.amunet_expiration_text = False
                rec.amunet_sys_weighing_range = False
                rec.quality_analysis_status = 'none'
                rec.solution_expiration_date = False
                continue

            product = rec.product_id
            rec.quality_ph_initial = product.amunet_initial_ph
            rec.amunet_expiration_text = product.amunet_expiration_text
            rec.amunet_sys_weighing_range = product.amunet_weighing_range_text

            if product.amunet_req_quality_control:
                rec.quality_analysis_status = 'to_request'
            else:
                rec.quality_analysis_status = 'none'

            if product.amunet_expiration_text:
                txt = product.amunet_expiration_text.lower()
                from datetime import timedelta
                days_to_add = 0
                try:
                    val = float(''.join(c for c in txt if c.isdigit() or c == '.'))
                    if 'mes' in txt: days_to_add = val * 30
                    elif 'año' in txt or 'ano' in txt: days_to_add = val * 365
                    elif 'dia' in txt or 'día' in txt: days_to_add = val
                except:
                    pass
                if days_to_add > 0:
                    rec.solution_expiration_date = fields.Datetime.now() + timedelta(days=days_to_add)

    @api.onchange('product_id')
    def _onchange_product_expiration(self):
        """Asigna campos de caducidad/pH y garantiza enlace de BoM al cambiar producto"""
        from datetime import timedelta
        product = self.product_id
        if not product:
            self.solution_expiration_date = False
            self.amunet_expiration_text = False
            self.quality_ph_initial = False
            self.bom_id = False
            return

        # Forzar enlace de BoM si no esta asignado (Odoo 19: el metodo nativo puede no correr antes)
        if not self.bom_id:
            bom_results = self.env['mrp.bom']._bom_find(
                product,
                company_id=self.company_id,
                bom_type='normal',
            )
            bom = bom_results.get(product, False)
            if bom:
                self.bom_id = bom

        self.amunet_expiration_text = product.amunet_expiration_text
        self.quality_ph_initial = product.amunet_initial_ph

        days_to_add = 0
        if product.amunet_expiration_text:
            txt = product.amunet_expiration_text.lower()
            try:
                val = float(''.join(c for c in txt if c.isdigit() or c == '.'))
                if 'mes' in txt: days_to_add = val * 30
                elif 'año' in txt or 'ano' in txt: days_to_add = val * 365
                elif 'dia' in txt or 'día' in txt: days_to_add = val
            except:
                pass
        self.solution_expiration_date = fields.Datetime.now() + timedelta(days=days_to_add) if days_to_add > 0 else False

    @api.onchange('product_id', 'product_qty', 'product_uom_id')
    def _onchange_amunet_product_setup(self):
        if not self.product_id:
            return
            
        product = self.product_id

        # Leer la receta (BoM) para encontrar todos los reactivos y verificar su inventario vs la cantidad a producir
        warnings = []
        bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', product.product_tmpl_id.id), '|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)], limit=1)
        if bom:
            # Conversion nativa UoM
            if self.product_uom_id and bom.product_uom_id:
                production_qty_bom_uom = self.product_uom_id._compute_quantity(self.product_qty or 1.0, bom.product_uom_id)
            else:
                production_qty_bom_uom = self.product_qty or 1.0
                
            bom_factor = production_qty_bom_uom / bom.product_qty if bom.product_qty else 1.0
            
            for line in bom.bom_line_ids:
                comp = line.product_id
                required_qty = line.product_qty * bom_factor
                
                # Odoo guarda los productos en su unidad base (ej. Unidades), pero la Lista pide otra unidad (ej. gramos)
                # Siempre se debe convertir el stock existente a la unidad que pide la receta para hacer algebra limpia:
                if comp.uom_id and line.product_uom_id and comp.uom_id != line.product_uom_id:
                    try:
                        available_qty = comp.uom_id._compute_quantity(comp.qty_available, line.product_uom_id)
                    except:
                        available_qty = comp.qty_available
                else:
                    available_qty = comp.qty_available
                
                if available_qty < required_qty:
                    missing_qty = required_qty - available_qty
                    # Diferenciar entre solucion hija y reactivo normal
                    if comp.categ_id and 'Solucion' in comp.categ_id.name:
                        warnings.append(f"CRITICO - Solucion Faltante: '{comp.name}'. Se requiere: {round(required_qty, 3)} pero solo hay: {round(available_qty, 3)} {line.product_uom_id.name}.")
                    else:
                        warnings.append(f"REACTIVO FALTANTE: '{comp.name}'. Falta comprar/surtir: {round(missing_qty, 3)} {line.product_uom_id.name}.")

        if warnings:
            return {
                'warning': {
                    'title': 'Analisis de Disponibilidad de Inventario',
                    'message': '\n'.join(warnings)
                }
            }

    @api.depends('move_raw_ids.amunet_is_valid')
    def _compute_all_ingredients_valid(self):
        for record in self:
            if not record.move_raw_ids:
                record.amunet_all_ingredients_valid = False
            else:
                record.amunet_all_ingredients_valid = all(move.amunet_is_valid for move in record.move_raw_ids)

    def action_request_analysis(self):
        """Valida estado/reactivos y abre el Wizard de análisis"""
        self.ensure_one()

        if self.quality_analysis_status not in ('none', 'to_request', 'rejected'):
            raise UserError('El análisis de calidad ya fue solicitado o se encuentra aprobado.')

        # Validar que todos los reactivos tengan cantidad utilizada
        sin_cantidad = self.move_raw_ids.filtered(lambda m: not m.quantity or m.quantity <= 0)
        if sin_cantidad:
            nombres = ', '.join(sin_cantidad.mapped('product_id.name'))
            raise UserError(f'Los siguientes reactivos no tienen Cantidad Utilizada registrada:\n{nombres}\n\nIngresa el valor antes de confirmar el análisis.')

        if not self.amunet_all_ingredients_valid:
            raise UserError('Todos los reactivos deben estar marcados como Válidos para proceder.')
        
        return {
            'name': 'Confirmar Solicitud de Análisis',
            'type': 'ir.actions.act_window',
            'res_model': 'amunet.production.analysis.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_production_id': self.id,
            }
        }
    
    def button_mark_done(self):
        """Bloqueo del flujo nativo de la orden de producción"""
        for record in self:
            # 1. Validar cantidades utilizadas en reactivos
            sin_cantidad = record.move_raw_ids.filtered(lambda m: not m.quantity or m.quantity <= 0)
            if sin_cantidad:
                nombres = ', '.join(sin_cantidad.mapped('product_id.name'))
                raise UserError(f'ATENCIÓN: Los siguientes reactivos no tienen Cantidad Utilizada:\n{nombres}\n\nCompleta los valores antes de marcar como hecho.')

            # 2. Validar Checklist Operativa
            missing = []
            if record.amunet_sys_req_history and not record.amunet_check_history_log: missing.append("Registro en Bitácoras")
            if record.amunet_sys_req_calc and not record.amunet_check_calculations: missing.append("Cálculos Realizados")
            if record.amunet_sys_req_dilution and not record.amunet_check_dilution: missing.append("Dilución de Reactivos")
            if record.amunet_sys_req_aforar and not record.amunet_check_aforar: missing.append("Aforar")
            if missing:
                raise UserError('ATENCIÓN: Faltan las siguientes actividades operativas por marcar en la Pestaña de Actividades:\n- ' + '\n- '.join(missing))
            
            # 2. Validar Calidad (solo si el producto lo requiere)
            if record.amunet_sys_req_qc and record.quality_analysis_status != 'approved':
                raise UserError('ATENCIÓN: Este producto requiere Análisis C.C. No puedes "Marcar como Hecho" hasta que el área de Calidad apruebe el análisis.')
                
        return super(MrpProduction, self).button_mark_done()
