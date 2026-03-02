# -*- coding: utf-8 -*-
from odoo import models, fields


class AmunetQualityCAPAExt(models.Model):
    """
    Extensión de amunet.quality.capa para añadir trazabilidad de auditorías.
    Este archivo vive en amunet_auditorias — NO modifica ningún archivo de amunet_quality.

    Los campos added_by son readonly: solo se pueblan automáticamente desde
    AmunetAuditoriaHallazgo.action_crear_capa().
    """
    _inherit = 'amunet.quality.capa'

    # Overrida product_id para que no sea requerido en CAPAs de auditoría.
    # Las auditorías de proceso/proveedor no están vinculadas a un producto específico.
    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        required=False,
        help='Producto relacionado (opcional en CAPAs originadas por auditorías)'
    )

    source_audit_id = fields.Many2one(
        'amunet.auditoria',
        string='Auditoría Origen',
        readonly=True,
        ondelete='set null',
        help='Auditoría de la cual se originó esta CAPA'
    )

    source_hallazgo_id = fields.Many2one(
        'amunet.auditoria.hallazgo',
        string='Hallazgo Origen',
        readonly=True,
        ondelete='set null',
        help='Hallazgo específico de la auditoría que generó esta CAPA'
    )

    audit_partner_id = fields.Many2one(
        'res.partner',
        string='Proveedor Auditado',
        readonly=True,
        ondelete='set null',
        help='Proveedor que fue auditado y generó el hallazgo'
    )
