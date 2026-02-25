# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    """
    Extensión de product.template para Control de Calidad.

    Agrega campos para configurar los parámetros de calidad,
    el tipo de prueba (destructiva/no destructiva) y la información
    de documentos de control de calidad.

    Epic-031: Sistema de Parámetros de Calidad Jerárquicos
    - Nueva relación One2many para configuración detallada por especificación
    """
    _inherit = 'product.template'

    # ========== Configuración de Control de Calidad ==========

    qc_required = fields.Boolean(
        string='Requiere control de calidad',
        default=False,
        help='Si está activo, se creará un QC automáticamente al recibir este producto'
    )

    qc_test_destructiveness = fields.Selection([
        ('non_destructive', 'No destructiva'),
        ('destructive', 'Destructiva'),
    ], string='Tipo de prueba', default='non_destructive',
        help='Define el flujo de inventario al finalizar el QC:\n'
             '- No destructiva: La muestra se devuelve a existencias\n'
             '- Destructiva: La cantidad analizada se envía a scrap')

    # ========== Relación con Parámetros (NUEVA - Epic-031) ==========

    qc_parameter_rel_ids = fields.One2many(
        'amunet.quality.parameter.product.rel',
        'product_tmpl_id',
        string='Parámetros de Calidad',
        help='Parámetros de QC configurados para este producto con especificaciones detalladas'
    )

    qc_parameter_count = fields.Integer(
        string='Cant. Parámetros',
        compute='_compute_qc_parameter_count',
        store=True
    )

    # ========== Campos de Conteo ==========

    qc_check_count = fields.Integer(
        string='Controles de calidad',
        compute='_compute_qc_check_count'
    )

    @api.depends('qc_parameter_rel_ids')
    def _compute_qc_parameter_count(self):
        """Cuenta los parámetros de QC configurados"""
        for record in self:
            record.qc_parameter_count = len(record.qc_parameter_rel_ids)

    def _compute_qc_check_count(self):
        """Cuenta los QC asociados a cada producto"""
        for record in self:
            record.qc_check_count = self.env['amunet.quality.check'].search_count([
                ('product_id.product_tmpl_id', '=', record.id)
            ])

    # ========================================================================
    # DOCUMENTOS DE CONTROL DE CALIDAD
    # Campos estáticos que se actualizan cuando se finaliza un reporte/QC
    # ========================================================================

    # ---------- REPORTE DE ANÁLISIS ----------

    report_document_header = fields.Selection([
        ('materia_prima', 'Materia prima'),
        ('producto_terminado', 'Producto terminado'),
        ('insumo', 'Insumo'),
    ], string='Encabezado (Reporte)',
        help='Tipo de producto del último reporte finalizado')

    report_effective_date = fields.Date(
        string='Fecha de elaboración (Reporte)',
        help='Fecha de elaboración del último reporte finalizado'
    )

    report_expiry_date = fields.Date(
        string='Fecha de vigencia (Reporte)',
        help='Fecha de vigencia del último reporte finalizado'
    )

    report_document_code = fields.Char(
        string='Código (Reporte)',
        help='Código del último reporte finalizado'
    )

    report_version = fields.Integer(
        string='Versión (Reporte)',
        help='Versión del último reporte finalizado'
    )

    report_replaces_version = fields.Integer(
        string='Sustituye (Reporte)',
        help='Versión que sustituye del último reporte finalizado'
    )

    report_references = fields.Text(
        string='Referencias (Reporte)',
        help='Referencias del último reporte finalizado'
    )

    # ---------- CERTIFICADO DE CALIDAD ----------

    certificate_document_header = fields.Selection([
        ('materia_prima', 'Materia prima'),
        ('producto_terminado', 'Producto terminado'),
        ('insumo', 'Insumo'),
    ], string='Encabezado (Certificado)',
        help='Tipo de producto del último certificado finalizado')

    certificate_effective_date = fields.Date(
        string='Fecha de elaboración (Certificado)',
        help='Fecha de elaboración del último certificado finalizado'
    )

    certificate_expiry_date = fields.Date(
        string='Fecha de vigencia (Certificado)',
        help='Fecha de vigencia del último certificado finalizado'
    )

    certificate_document_code = fields.Char(
        string='Código (Certificado)',
        help='Código del último certificado finalizado'
    )

    certificate_version = fields.Integer(
        string='Versión (Certificado)',
        help='Versión del último certificado finalizado'
    )

    certificate_replaces_version = fields.Integer(
        string='Sustituye (Certificado)',
        help='Versión que sustituye del último certificado finalizado'
    )

    # ========== Acciones ==========

    def action_view_quality_checks(self):
        """Abre los controles de calidad del producto"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Controles de calidad',
            'res_model': 'amunet.quality.check',
            'view_mode': 'list,form',
            'domain': [('product_id.product_tmpl_id', '=', self.id)],
            'context': {'default_product_id': self.product_variant_id.id},
        }

    def action_view_qc_parameters(self):
        """Abre los parámetros de QC configurados"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Parámetros QC - {self.name}',
            'res_model': 'amunet.quality.parameter.product.rel',
            'view_mode': 'list,form',
            'domain': [('product_tmpl_id', '=', self.id)],
            'context': {'default_product_tmpl_id': self.id},
        }

    # ========== Métodos de Utilidad ==========

    def get_qc_parameters_for_check(self):
        """
        Obtiene los parámetros configurados para crear un QC.
        
        Returns:
            recordset: amunet.quality.parameter.product.rel con parámetros activos
        """
        self.ensure_one()
        return self.qc_parameter_rel_ids.filtered(
            lambda rel: rel.parameter_id.active
        ).sorted('sequence')

    def get_active_specifications(self):
        """
        Obtiene todas las especificaciones activas de todos los parámetros.

        Returns:
            recordset: amunet.quality.parameter.specification.config
        """
        self.ensure_one()
        configs = self.env['amunet.quality.parameter.specification.config']
        for rel in self.qc_parameter_rel_ids:
            configs |= rel.get_active_specifications()
        return configs

    # ========================================================================
    # EPIC-032: INFORMACIÓN ADICIONAL EN CONTROL DE CALIDAD
    # Campos informativos que NO afectan el dictamen global del QC
    # ========================================================================

    require_additional_info = fields.Boolean(
        string='Información adicional',
        default=False,
        help='Activar para configurar campos informativos que se capturarán en el QC de este producto'
    )

    additional_info_config_ids = fields.One2many(
        comodel_name='amunet.quality.additional.info.config',
        inverse_name='product_tmpl_id',
        string='Configuración de información adicional',
        help='Campos informativos que se capturarán en el QC'
    )

    @api.onchange('require_additional_info')
    def _onchange_require_additional_info(self):
        """
        Al activar 'Información adicional', pre-cargar los 3 campos por defecto
        si no existen configuraciones previas
        """
        if self.require_additional_info and not self.additional_info_config_ids:
            # Obtener todos los campos activos del catálogo
            available_fields = self.env['amunet.quality.additional.info.field'].search(
                [('active', '=', True)],
                order='sequence'
            )

            # Crear configuración por defecto (sin guardar en BD aún)
            config_vals = []
            for idx, field in enumerate(available_fields):
                config_vals.append((0, 0, {
                    'field_id': field.id,
                    'required': False,  # Usuario decide cuáles son obligatorios
                    'active': True,     # Todos visibles por defecto
                    'sequence': (idx + 1) * 10,
                }))

            self.additional_info_config_ids = config_vals

    @api.onchange('qc_required')
    def _onchange_qc_required(self):
        """
        Si se desactiva 'Requiere Control de Calidad',
        automáticamente desactivar 'Información adicional'
        """
        if not self.qc_required and self.require_additional_info:
            self.require_additional_info = False

    @api.constrains('require_additional_info', 'qc_required')
    def _check_additional_info_requires_qc(self):
        """
        No se puede activar 'Información adicional' sin tener activo
        'Requiere Control de Calidad'
        """
        from odoo.exceptions import ValidationError

        for product in self:
            if product.require_additional_info and not product.qc_required:
                raise ValidationError(
                    f"El producto '{product.name}' no puede tener 'Información adicional' "
                    "activada sin tener 'Requiere Control de Calidad' activo.\n\n"
                    "Por favor, active primero 'Requiere Control de Calidad'."
                )
