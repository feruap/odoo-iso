# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    is_quality_control = fields.Boolean(
        string='Es Control de Calidad',
        default=False,
        help='Marcar si este tipo de operación es para control de calidad.'
    )

    is_reception = fields.Boolean(
        string='Es recepción',
        default=False,
        help='Marcar si este tipo de operación es para recepción.'
    )

    is_storage = fields.Boolean(
        string='Es almacenamiento',
        default=False,
        help='Marcar si este tipo de operación es para almacenamiento.'
    )

    @api.model
    def _setup_amunet_operation_types(self):
        """
        Configura automáticamente los tipos de operación al instalar el módulo.

        - is_reception = True para tipos con code='incoming'
        - is_quality_control = True para tipos con 'control de calidad' en el nombre
        - is_storage = True para tipos con 'almacenamiento' en el nombre

        IMPORTANTE: Solo actualiza registros donde los campos estén en False/None.
        NO sobrescribe valores configurados manualmente.
        """
        # Configurar tipos de recepción (incoming)
        reception_types = self.search([
            ('code', '=', 'incoming'),
            '|', ('is_reception', '=', False), ('is_reception', '=', None)
        ])
        if reception_types:
            reception_types.write({'is_reception': True})
            _logger.info(
                '✓ Configurados %s tipos de recepción (is_reception=True)',
                len(reception_types)
            )

        # Configurar tipos de control de calidad
        qc_types = self.search([
            ('code', '=', 'internal'),
            '|',
            ('name', 'ilike', 'control de calidad'),
            ('name', 'ilike', 'quality control'),
            '|', ('is_quality_control', '=', False),
            ('is_quality_control', '=', None)
        ])
        if qc_types:
            qc_types.write({'is_quality_control': True})
            _logger.info(
                '✓ Configurados %s tipos de control de calidad '
                '(is_quality_control=True)',
                len(qc_types)
            )

        # Configurar tipos de almacenamiento
        storage_types = self.search([
            ('code', '=', 'internal'),
            '|',
            ('name', 'ilike', 'almacenamiento'),
            ('name', 'ilike', 'storage'),
            '|', ('is_storage', '=', False), ('is_storage', '=', None)
        ])
        if storage_types:
            storage_types.write({'is_storage': True})
            _logger.info(
                '✓ Configurados %s tipos de almacenamiento (is_storage=True)',
                len(storage_types)
            )

        return True
