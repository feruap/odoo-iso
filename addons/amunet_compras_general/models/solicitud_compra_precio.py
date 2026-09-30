# -*- coding: utf-8 -*-
"""Precio en el renglon de la solicitud de compra.

Regla de Direccion (30-sep-2026): si un renglon trae liga de compra
(Amazon, Mercado Libre, AliExpress, eBay...), tiene que traer precio.

El motivo es el circuito de autorizacion, no la contabilidad. Quien
autoriza una compra ve el folio, lo que se pide y el importe; si el
importe viene vacio esta firmando en blanco. SC/2026/00002 llego
aprobada con cuatro renglones de Amazon y eBay y cero pesos de
importe: nadie podia saber si autorizaba dos mil o veinte mil.

El precio de una liga NO es dato confidencial: lo teclea quien pide,
copiado de una pagina publica. Por eso va sin `groups=`, al contrario
de `amunet_monto`, que es el importe que se va a pagar y sigue
reservado al area de compras.
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


def _con_liga_sin_precio(lineas):
    """Renglones que traen liga de compra y no traen precio."""
    return lineas.filtered(
        lambda l: (l.purchase_url or '').strip()
        and not l.amunet_precio_unitario
    )


class AmunetSolicitudCompraLine(models.Model):
    _inherit = 'amunet.solicitud.compra.line'

    amunet_precio_unitario = fields.Float(
        string='Precio unitario',
        digits='Product Price',
        help='El precio que aparece en la liga de compra, por unidad. '
             'Obligatorio cuando el renglon trae liga: sin precio nadie '
             'puede autorizar la compra.',
    )
    amunet_importe_linea = fields.Float(
        string='Importe',
        compute='_compute_amunet_importe_linea',
        store=True,
        digits='Product Price',
    )

    @api.depends('qty', 'amunet_precio_unitario')
    def _compute_amunet_importe_linea(self):
        for linea in self:
            linea.amunet_importe_linea = (
                (linea.qty or 0.0) * (linea.amunet_precio_unitario or 0.0)
            )

    @api.constrains('purchase_url', 'amunet_precio_unitario')
    def _check_precio_si_hay_liga(self):
        """En borrador se deja capturar a medias; al enviarla ya no."""
        for linea in _con_liga_sin_precio(self):
            if linea.request_id.state == 'draft':
                continue
            raise ValidationError(_(
                'El renglon "%s" trae liga de compra pero no trae precio.\n\n'
                'Sin precio nadie puede autorizar la compra: quien firma '
                'necesita saber cuanto cuesta. Captura el precio unitario '
                'que aparece en la liga.'
            ) % (linea.name or '?'))


class AmunetSolicitudCompra(models.Model):
    _inherit = 'amunet.solicitud.compra'

    amunet_total_lineas = fields.Float(
        string='Total de los renglones',
        compute='_compute_amunet_total_lineas',
        store=True,
        digits='Product Price',
        help='Suma de los renglones con precio capturado. Es la referencia '
             'de lo que se va a gastar, antes de envio e impuestos.',
    )

    @api.depends('line_ids.amunet_importe_linea')
    def _compute_amunet_total_lineas(self):
        for req in self:
            req.amunet_total_lineas = sum(
                req.line_ids.mapped('amunet_importe_linea'))

    def action_enviar(self):
        """No sale de borrador una solicitud con ligas sin precio.

        El candado va aqui y no solo en el constrains porque este es el
        momento en que la solicitud deja de ser un borrador de quien pide
        y se convierte en algo que otro tiene que firmar.
        """
        for req in self:
            faltan = _con_liga_sin_precio(req.line_ids)
            if faltan:
                raise ValidationError(_(
                    'Falta el precio en %s renglon(es) de %s que traen liga '
                    'de compra:\n\n%s\n\n'
                    'Captura el precio que aparece en cada liga. Quien '
                    'autoriza no puede firmar una compra sin importe.'
                ) % (len(faltan), req.name,
                     '\n'.join('- %s' % (l.name or '?') for l in faltan)))
        resultado = super().action_enviar()
        # El encabezado lleva el importe que ve quien autoriza. Si nadie lo
        # capturo a mano pero los renglones ya traen precio, se siembra con
        # la suma: es el dato que el bot de Telegram pone en la orden.
        for req in self:
            if req.amunet_total_lineas and not req.sudo().amunet_monto:
                req.sudo().amunet_monto = req.amunet_total_lineas
                req.message_post(body=_(
                    'Importe tomado de los renglones: %s'
                ) % '{:,.2f}'.format(req.amunet_total_lineas))
        return resultado
