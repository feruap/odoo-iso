# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AmunetQualityAdditionalInfoField(models.Model):
    _name = 'amunet.quality.additional.info.field'
    _description = 'Campo de Información Adicional en QC'
    _order = 'sequence, name'

    code = fields.Char(
        string='Código técnico',
        index=True,
        readonly=True,
        copy=False,
        help='Identificador técnico auto-generado desde el nombre'
    )

    name = fields.Char(
        string='Nombre',
        required=True,
        translate=True,
        help='Nombre del campo informativo'
    )

    field_type = fields.Selection(
        selection=[
            ('decimal', 'Numérico decimal'),
            ('percentage', 'Porcentaje'),
            ('html_attachments', 'Texto con adjuntos'),
        ],
        string='Tipo de campo',
        required=True,
        help='Tipo de dato que almacenará este campo'
    )

    uom = fields.Char(
        string='Unidad de medida',
        help='Unidad (ej: cm, %, kg). Opcional.'
    )

    placeholder = fields.Char(
        string='Texto de ayuda (placeholder)',
        translate=True,
        help='Texto que aparecerá como guía en el campo del QC (ej: "Escriba aquí las observaciones...")'
    )

    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Desactivar para ocultar del sistema'
    )

    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de visualización (menor = primero)'
    )

    @api.constrains('code')
    def _check_code_unique(self):
        """Validar que el código sea único."""
        for record in self:
            if record.code:
                existing = self.search([
                    ('code', '=', record.code),
                    ('id', '!=', record.id),
                ], limit=1)
                if existing:
                    raise ValidationError('El código del campo debe ser único.')

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-genera código desde nombre si no se proporciona"""
        for vals in vals_list:
            if not vals.get('code') and vals.get('name'):
                vals['code'] = self._generate_code_from_name(vals['name'])

            # Validar restricción de campos tipo "Texto con adjuntos"
            if vals.get('field_type') == 'html_attachments':
                self._check_html_attachments_limit()

        return super().create(vals_list)

    def write(self, vals):
        """Regenera código si cambia el nombre y el código estaba auto-generado"""
        if 'name' in vals and not vals.get('code'):
            for record in self:
                # Solo regenerar si el código actual parece auto-generado
                if record.code and '_' in record.code:
                    vals['code'] = self._generate_code_from_name(vals['name'])

        # Validar si se está cambiando a tipo "Texto con adjuntos"
        if 'field_type' in vals and vals['field_type'] == 'html_attachments':
            for record in self:
                # Si el registro ya es html_attachments, permitir
                if record.field_type != 'html_attachments':
                    self._check_html_attachments_limit()

        return super().write(vals)

    def _check_html_attachments_limit(self):
        """
        Valida que solo exista un campo activo de tipo 'Texto con adjuntos'.

        Raises:
            ValidationError: Si ya existe un campo de tipo html_attachments
        """
        existing_count = self.search_count([
            ('field_type', '=', 'html_attachments'),
            ('active', '=', True),
        ])

        if existing_count >= 1:
            raise ValidationError(
                'Solo se permite un campo de tipo "Texto con adjuntos" en el sistema.\n\n'
                'Ya existe un campo de este tipo. Si desea crear uno nuevo, '
                'primero debe archivar el campo existente.'
            )

    @api.model
    def _generate_code_from_name(self, name):
        """
        Genera un código técnico desde el nombre del campo.

        Ejemplos:
        - "Promedio de largo" → "promedio_largo"
        - "Coeficiente de variación" → "coeficiente_variacion"
        - "Observaciones generales" → "observaciones_generales"

        :param name: Nombre del campo
        :return: Código técnico slugified
        """
        if not name:
            return 'field'

        # Convertir a minúsculas
        code = name.lower()

        # Remover acentos y caracteres especiales
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u',
        }
        for old, new in replacements.items():
            code = code.replace(old, new)

        # Reemplazar espacios y caracteres no alfanuméricos con guión bajo
        code = re.sub(r'[^a-z0-9]+', '_', code)

        # Remover guiones bajos al inicio/final
        code = code.strip('_')

        # Limitar longitud
        code = code[:50]

        # Asegurar unicidad
        base_code = code
        counter = 1
        while self.search([('code', '=', code)], limit=1):
            code = f'{base_code}_{counter}'
            counter += 1

        return code

    @api.model
    def _get_field_widget(self, field_type):
        """
        Retorna el widget XML recomendado según tipo de campo

        :param field_type: Tipo de campo ('decimal', 'percentage', etc.)
        :return: Nombre del widget Odoo
        """
        widget_map = {
            'decimal': 'float',
            'percentage': 'percentage',
            'html_attachments': 'html',
        }
        return widget_map.get(field_type, 'char')
