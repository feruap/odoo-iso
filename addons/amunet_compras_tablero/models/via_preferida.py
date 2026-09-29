# -*- coding: utf-8 -*-
"""Via de embarque que PREFIERE el solicitante (avion o barco).

Pedido de Fernando, 29-sep-2026. Es una preferencia, no una orden: la via
final (amunet_via_embarque en la orden de compra) la sigue decidiendo
Compras, porque Compras paga el flete. Aqui solo queda escrito lo que pidio
quien necesita el material, para que Compras lo vea en la orden y en el
tablero sin tener que preguntar.

Vive en este modulo y no en amunet_compras_general para no mezclarse con
cambios de ese modulo que todavia no pasan a produccion.
"""

from odoo import api, fields, models

VIA_PREFERIDA = [
    ('aereo', 'Avion (aereo)'),
    ('maritimo', 'Barco (maritimo)'),
]


class AmunetSolicitudCompraVia(models.Model):
    _inherit = 'amunet.solicitud.compra'

    amunet_via_preferida = fields.Selection(
        selection=VIA_PREFERIDA,
        string='Prefiero que llegue por',
        tracking=True,
        help='Tu preferencia. Avion es mas rapido y mas caro; barco tarda '
             'semanas pero cuesta menos. La decision final la toma Compras.',
    )


class PurchaseOrderVia(models.Model):
    _inherit = 'purchase.order'

    amunet_via_preferida = fields.Selection(
        selection=VIA_PREFERIDA,
        string='Via que pidio el solicitante',
        compute='_compute_amunet_via_preferida',
        help='Lo que pidieron las solicitudes ligadas. Si una sola pide '
             'avion, se muestra avion.',
    )

    @api.depends('amunet_solicitud_compra_ids.amunet_via_preferida')
    def _compute_amunet_via_preferida(self):
        for orden in self:
            prefs = set(filter(None, orden.sudo().amunet_solicitud_compra_ids
                               .mapped('amunet_via_preferida')))
            if 'aereo' in prefs:
                orden.amunet_via_preferida = 'aereo'
            elif prefs:
                orden.amunet_via_preferida = 'maritimo'
            else:
                orden.amunet_via_preferida = False
