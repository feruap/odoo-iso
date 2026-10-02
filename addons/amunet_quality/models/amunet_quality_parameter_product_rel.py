# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AmunetQualityParameterProductRel(models.Model):
    """
    Relación Producto-Parámetro de Calidad.

    Tabla intermedia que vincula productos con parámetros de calidad,
    permitiendo configurar especificaciones específicas por producto.

    Epic-031: Sistema de Parámetros de Calidad Jerárquicos
    T-031-4: Crear relación producto-parámetro-especificación
    """
    _name = 'amunet.quality.parameter.product.rel'
    _description = 'Relación Producto-Parámetro de Calidad'
    _order = 'sequence, id'
    _rec_name = 'display_name'

    # ========== Relaciones Principales ==========

    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Producto',
        required=True,
        ondelete='cascade',
        index=True
    )

    parameter_id = fields.Many2one(
        'amunet.quality.check.parameter',
        string='Parámetro',
        required=True,
        ondelete='restrict',
        index=True
    )

    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden del parámetro en el producto'
    )

    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Indica si esta configuración de parámetro está activa.'
    )

    # ========== Configuración de Especificaciones ==========

    specification_config_ids = fields.One2many(
        'amunet.quality.parameter.specification.config',
        'product_parameter_rel_id',
        string='Configuración de especificaciones',
        help='Configuración específica de cada especificación para este producto'
    )

    # ========== Campos Relacionados (para mostrar en vistas) ==========

    parameter_code = fields.Char(
        string='Código',
        related='parameter_id.code',
        store=True
    )

    parameter_name = fields.Char(
        string='Determinación',
        related='parameter_id.name',
        store=True
    )

    specification_total = fields.Integer(
        string='Esp. Totales',
        related='parameter_id.specification_count'
    )

    # ========== Campos Computados ==========

    active_spec_count = fields.Integer(
        string='Esp. Activas',
        compute='_compute_active_spec_count',
        store=True
    )

    spec_summary = fields.Char(
        string='Resumen',
        compute='_compute_spec_summary',
        store=True
    )

    display_name = fields.Char(
        string='Nombre',
        compute='_compute_display_name',
        store=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        related='product_tmpl_id.company_id',
        store=True
    )

    @api.depends('specification_config_ids', 'specification_config_ids.active')
    def _compute_active_spec_count(self):
        """Cuenta las especificaciones activas para este producto"""
        for record in self:
            record.active_spec_count = len(
                record.specification_config_ids.filtered(lambda c: c.active)
            )

    @api.depends('specification_config_ids', 'specification_config_ids.nominal_value', 
                 'specification_config_ids.max_value_manual', 'specification_config_ids.acceptance_criteria')
    def _compute_spec_summary(self):
        """Genera resumen de especificaciones con valores: 'Ancho: 18, Largo: 48'"""
        # Prefetch de configuraciones para todos los registros procesados
        self.specification_config_ids.mapped('specification_id') # Trigger prefetch
        
        for record in self:
            # Filtrar solo las que tienen algún valor real configurado
            configs = record.specification_config_ids.filtered(
                lambda s: s.active
            )
            
            if not configs:
                record.spec_summary = "Sin valores"
                continue

            summary_parts = []
            # Tomar las primeras 3 para no saturar la vista de lista
            for config in configs[:3]:
                name = config.specification_id.name or "?"
                if config.evaluation_type == 'numeric_range':
                    if config.nominal_value > 0:
                        val = f"{config.nominal_value}"
                    elif config.max_value_manual > 0:
                        val = f"<{config.max_value_manual}"
                    elif config.min_value_manual > 0:
                        val = f">{config.min_value_manual}"
                    else:
                        val = "?"
                elif config.evaluation_type == 'binary_selection':
                    val = config.binary_option_pass or "OK"
                elif config.acceptance_criteria:
                    val = "OK"
                else:
                    val = "..."
                summary_parts.append(f"{name}: {val}")
            
            suffix = "..." if len(configs) > 3 else ""
            record.spec_summary = ", ".join(summary_parts) + suffix

    @api.depends('parameter_code', 'parameter_name')
    def _compute_display_name(self):
        """Genera nombre para mostrar: '[CÓDIGO] Determinación'"""
        for record in self:
            parts = []
            if record.parameter_code:
                parts.append(f'[{record.parameter_code}]')
            if record.parameter_name:
                parts.append(record.parameter_name)
            record.display_name = ' '.join(parts) if parts else 'Parámetro'

    # ========== Métodos de Acción ==========

    def action_configure_specifications(self):
        """Abre wizard/modal para configurar especificaciones del parámetro para este producto"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Configurar: {self.display_name}',
            'res_model': 'amunet.quality.parameter.product.rel',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # ========== Onchange ==========

    @api.onchange('parameter_id')
    def _onchange_parameter_id(self):
        """Al seleccionar parámetro, genera configuraciones para sus especificaciones"""
        if self.parameter_id:
            # Esto se ejecutará al guardar, no en onchange
            # Ver método create() y write()
            pass

    # ==================================================================
    # AUDITORIA DEL BLOQUE
    # ==================================================================
    # Apagar un BLOQUE entero quita del analisis todas sus especificaciones de
    # golpe, asi que necesita el mismo rastro que apagar una sola -- y la misma
    # razon de cambio. Hasta el 2-oct-2026 este modelo no auditaba nada.
    #
    # Es el hermano del hueco que encontro el chequeo del 2-oct: 72
    # especificaciones apagadas en ocho meses sin una sola linea de auditoria.
    # Ver el encabezado de amunet_quality_parameter_specification_config.py.
    #
    # Razon de cambio exigida SOLO al desactivar. Decision de Mery, 2-oct-2026.
    # ==================================================================

    change_reason = fields.Char(
        string='Razón de cambio',
        help='Obligatoria para DESACTIVAR un bloque. Apagarlo quita del análisis '
             'todas sus especificaciones a la vez.')

    def _amunet_describe_bloque(self):
        self.ensure_one()
        prod = self.product_tmpl_id.default_code or self.product_tmpl_id.name or '?'
        return '%s / %s' % (prod, self.parameter_id.name or '?')

    def _amunet_asentar_bloque(self, campo, antes, despues, motivo):
        self.ensure_one()
        self.env['amunet.quality.audit.log'].sudo().create({
            'model_name': self._name,
            'res_id': self.id,
            'res_name': self._amunet_describe_bloque(),
            'field_name': campo,
            'old_value': antes,
            'new_value': despues,
            'justification': motivo,
            'user_id': self.env.user.id,
        })

    def write(self, vals):
        if 'active' in vals and not vals.get('active'):
            motivo = vals.get('change_reason')
            for rec in self:
                if rec.active and not (motivo or rec.change_reason):
                    n = self.env['amunet.quality.parameter.specification.config'].sudo(
                        ).search_count([('product_parameter_rel_id', '=', rec.id),
                                        ('active', '=', True)])
                    raise UserError(_(
                        'Para DESACTIVAR el bloque "%(desc)s" hace falta una razón '
                        'de cambio.\n\n'
                        'Se apagarían de golpe sus %(n)s especificación(es) activas en '
                        'todos los análisis futuros de ese producto. Escribe por qué '
                        'en "Razón de cambio".'
                    ) % {'desc': rec._amunet_describe_bloque(), 'n': n})

        activos_antes = {rec.id: rec.active for rec in self} if 'active' in vals else {}
        res = super().write(vals)
        if res and 'active' in vals:
            motivo_dado = vals.get('change_reason')
            for rec in self:
                if activos_antes.get(rec.id) == rec.active:
                    continue
                rec._amunet_asentar_bloque(
                    'active', str(activos_antes.get(rec.id)), str(rec.active),
                    motivo_dado or rec.change_reason or 'Cambio de configuración')
                if rec.change_reason:
                    super(AmunetQualityParameterProductRel,
                          rec.sudo()).write({'change_reason': False})
        return res

    # ========== Métodos CRUD ==========

    @api.model_create_multi
    def create(self, vals_list):
        """Al crear relación, genera configuraciones para las especificaciones del parámetro"""
        records = super().create(vals_list)
        for record in records:
            record._generate_specification_configs()
        return records

    def _generate_specification_configs(self):
        """
        Genera configuraciones de especificación para este producto-parámetro.
        Copia los valores por defecto desde la especificación base.
        """
        self.ensure_one()

        # Si ya tiene configuraciones, no regenerar
        if self.specification_config_ids:
            return

        if not self.parameter_id or not self.parameter_id.specification_line_ids:
            return

        SpecConfig = self.env['amunet.quality.parameter.specification.config']
        
        config_vals = []
        for spec in self.parameter_id.specification_line_ids:
            # Copiar TODOS los valores de la especificación como defaults
            vals = {
                'product_parameter_rel_id': self.id,
                'specification_id': spec.id,
                'active': True,
                'sequence': spec.sequence,
                # Criterio de aceptación
                'acceptance_criteria': spec.acceptance_criteria,
                'uom_id': spec.uom_id.id if spec.uom_id else False,
                # Binary selection
                'binary_prefix': spec.binary_prefix,
                'binary_suffix': spec.binary_suffix,
                'binary_expected_option': spec.binary_expected_option,
                # Checkbox combined
                'checkbox_label_1': spec.checkbox_label_1,
                'checkbox_label_2': spec.checkbox_label_2,
                'checkbox_require_both': spec.checkbox_require_both,
                # Text pattern
                'text_pattern_expected': spec.text_pattern_expected,
                'text_pattern_regex': spec.text_pattern_regex,
                'text_phrase_mapping': spec.text_phrase_mapping,
                # Expected vs Obtained
                'expected_options': spec.expected_options,
                'obtained_options': spec.obtained_options,
                # Binary with notes
                'binary_notes_option_pass': spec.binary_notes_option_pass,
                'binary_notes_option_fail': spec.binary_notes_option_fail,
                'binary_notes_required': spec.binary_notes_required,
                # Ternary
                'ternary_option_yes': spec.ternary_option_yes,
                'ternary_option_no': spec.ternary_option_no,
                'ternary_option_na': spec.ternary_option_na,
                # Numeric range (Added in personalization fix)
                'nominal_value': spec.nominal_value,
                'tolerance': spec.tolerance,
                'min_value_manual': spec.min_value_manual,
                'max_value_manual': spec.max_value_manual,
                'use_manual_range': spec.use_manual_range,
                'min_value': spec.min_value,
                'max_value': spec.max_value,
            }
            config_vals.append(vals)

        if config_vals:
            config_records = SpecConfig.create(config_vals)
            # Copiar opciones condicionales después de crear los registros
            for config_record, spec in zip(config_records, self.parameter_id.specification_line_ids):
                if spec.conditional_option_ids:
                    config_record.active_conditional_option_ids = spec.conditional_option_ids

    def action_regenerate_configs(self):
        """Regenera las configuraciones de especificación (elimina existentes)"""
        self.ensure_one()
        self.specification_config_ids.unlink()
        self._generate_specification_configs()
        return True

    # ========== Métodos de Utilidad ==========

    def get_active_specifications(self):
        """Retorna las especificaciones activas para este producto-parámetro"""
        self.ensure_one()
        return self.specification_config_ids.filtered(lambda c: c.active)

    @api.model
    def _migrate_soluciones_vama_to_mavi(self):
        """Migración VAMA→MAVI en soluciones de trabajo semiprocesado. Idempotente."""
        Tmpl = self.env['product.template']
        SpecConfig = self.env['amunet.quality.parameter.specification.config']
        cr = self.env.cr

        # Parámetros del catálogo
        MAVI_07_ID = self.env.ref('amunet_quality.param_mavi_07').id
        MAVI_13_ID = self.env.ref('amunet_quality.param_vama_004').id
        MGA_0701_ID = self.env.ref('amunet_quality.param_mga_0701').id

        # Specs de catálogo para MAVI-07 (Muestra negativa=628, positiva=629)
        mavi07_specs = self.env['amunet.quality.check.parameter.specification'].search([
            ('parameter_id', '=', MAVI_07_ID),
            ('name', 'in', ['Muestra negativa', 'Muestra positiva']),
            ('active', '=', True),
        ])

        # 1. VAMA-034 → MAVI-07 en 5 soluciones
        for code in ['SPAPB01', 'SPBAB01', 'SPBAB02', 'SPSAG01', 'SPHBB01']:
            tmpl = Tmpl.search([('default_code', '=', code), ('active', '=', True)], limit=1)
            if not tmpl:
                continue
            if self.search([('product_tmpl_id', '=', tmpl.id), ('parameter_id', '=', MAVI_07_ID)]):
                continue  # ya migrado
            # Desactivar VAMA-034
            self.search([
                ('product_tmpl_id', '=', tmpl.id),
                ('parameter_code', '=', 'VAMA-034'),
                ('active', '=', True),
            ]).write({'active': False})
            # Crear rel MAVI-07 via SQL para evitar el batch create problemático
            cr.execute("""
                INSERT INTO amunet_quality_parameter_product_rel
                    (product_tmpl_id, parameter_id, parameter_code, parameter_name,
                     active, create_uid, write_uid, create_date, write_date)
                VALUES (%s, %s, 'MAVI-07', 'Visualización de líneas resultado base',
                        TRUE, 1, 1, NOW(), NOW()) RETURNING id
            """, (tmpl.id, MAVI_07_ID))
            new_rel_id = cr.fetchone()[0]
            for spec in mavi07_specs:
                SpecConfig.create({
                    'product_parameter_rel_id': new_rel_id,
                    'specification_id': spec.id,
                    'active': True,
                })

        # 2. SPNPS01: renombrar VAMA → MAVI (solo si siguen con código VAMA)
        spnps01 = Tmpl.search([('default_code', '=', 'SPNPS01'), ('active', '=', True)], limit=1)
        if spnps01:
            renames = [
                ('VAMA-006', 'MAVI-03',  'Determinación de color NPS'),
                ('VAMA-065', 'MGA 0361', 'Espectrofotometría visible y ultravioleta'),
                ('VAMA-066', 'MAVI-16',  'Apariencia colorimétrica'),
                ('VAMA-067', 'MAVI-10',  'Apariencia y aglomeración después de las fuerzas centrífugas'),
            ]
            for old_code, new_code, new_name in renames:
                rel = self.search([
                    ('product_tmpl_id', '=', spnps01.id),
                    ('parameter_code', '=', old_code),
                    ('active', '=', True),
                ])
                if rel:
                    rel.write({'parameter_code': new_code, 'parameter_name': new_name})

        # 3. SPSPA05: agregar MAVI-13 y MGA 0701 si no existen
        spspa05 = Tmpl.search([('default_code', '=', 'SPSPA05'), ('active', '=', True)], limit=1)
        if spspa05:
            if not self.search([('product_tmpl_id', '=', spspa05.id), ('parameter_id', '=', MAVI_13_ID)]):
                spec_m13 = self.env['amunet.quality.check.parameter.specification'].search([
                    ('parameter_id', '=', MAVI_13_ID), ('active', '=', True),
                ], limit=1)
                if spec_m13:
                    cr.execute("""
                        INSERT INTO amunet_quality_parameter_product_rel
                            (product_tmpl_id, parameter_id, parameter_code, parameter_name,
                             active, create_uid, write_uid, create_date, write_date)
                        VALUES (%s, %s, 'MAVI-13', 'Examen de partículas',
                                TRUE, 1, 1, NOW(), NOW()) RETURNING id
                    """, (spspa05.id, MAVI_13_ID))
                    SpecConfig.create({
                        'product_parameter_rel_id': cr.fetchone()[0],
                        'specification_id': spec_m13.id,
                        'active': True,
                    })
            if not self.search([('product_tmpl_id', '=', spspa05.id), ('parameter_id', '=', MGA_0701_ID)]):
                spec_mga = self.env['amunet.quality.check.parameter.specification'].search([
                    ('parameter_id', '=', MGA_0701_ID),
                    ('evaluation_type', '=', 'numeric_range'),
                    ('active', '=', True),
                ], limit=1)
                if spec_mga:
                    cr.execute("""
                        INSERT INTO amunet_quality_parameter_product_rel
                            (product_tmpl_id, parameter_id, parameter_code, parameter_name,
                             active, create_uid, write_uid, create_date, write_date)
                        VALUES (%s, %s, 'MGA 0701', 'Determinación de pH',
                                TRUE, 1, 1, NOW(), NOW()) RETURNING id
                    """, (spspa05.id, MGA_0701_ID))
                    SpecConfig.create({
                        'product_parameter_rel_id': cr.fetchone()[0],
                        'specification_id': spec_mga.id,
                        'active': True,
                        'specification_name': 'pH',
                        'nominal_value': 8.6,
                        'tolerance': 0.05,
                        'min_value': 8.55,
                        'max_value': 8.65,
                    })

    def get_test_line_values(self):
        """
        Prepara los valores para crear una línea de test en el QC.
        
        Returns:
            dict: Valores para amunet.quality.test.line
        """
        self.ensure_one()
        return {
            'parameter_id': self.parameter_id.id,
            'name': self.parameter_id.name,
            'sequence': self.sequence,
            # Los detalles se generan desde las especificaciones activas
        }

