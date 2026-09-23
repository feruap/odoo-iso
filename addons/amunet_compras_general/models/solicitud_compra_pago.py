# -*- coding: utf-8 -*-
"""Datos de pago de una solicitud de compra (Marketplace interno).

Desde 19.0.5.0.0 estos campos viven en `amunet.solicitud.compra` y no en la
solicitud de material: pedirle material a Almacen y comprar en una tienda son
dos tramites distintos (decision de Mery, 19-sep-2026).

El monto es el unico dato sensible aqui. Se protege en dos capas:

  1. El campo almacenado `amunet_monto` lleva `groups=` a nivel ORM: para
     quien no esta en el grupo el campo NO EXISTE. No se lee por vista, ni
     por search_read, ni por API, ni por exportacion.
  2. El jefe que autoriza una solicitud necesita saber cuanto cuesta lo que
     firma, pero no tiene por que ver los montos de las demas areas. Para
     eso existe `amunet_monto_visible`: un campo calculado que se resuelve
     registro por registro y solo devuelve cifra a quien le corresponde.
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

GRUPO_MONTO = 'amunet_compras_general.group_compras_monto'


class AmunetSolicitudCompra(models.Model):
    _inherit = 'amunet.solicitud.compra'

    amunet_forma_pago = fields.Selection(
        selection=[
            ('tarjeta', 'Tarjeta (Amazon / Mercado Libre / AliExpress)'),
            ('transferencia', 'Transferencia bancaria'),
            ('otro', 'Otro / por definir'),
        ],
        string='Forma de pago',
        tracking=True,
        help='Decide el camino: con tarjeta la compra se hace en la tienda; '
             'con transferencia se avisa al grupo de pagos.',
    )
    # Decide desde que cuenta se paga: con factura, la cuenta de Amunet; sin
    # factura, la otra. El bot de pagos lo lee para redactar la orden.
    amunet_proveedor_factura = fields.Boolean(
        string='El proveedor factura', tracking=True,
        help='Si el proveedor emite factura (CFDI). Cambia desde que cuenta '
             'se paga.',
    )

    amunet_currency_id = fields.Many2one(
        'res.currency', string='Moneda',
        default=lambda self: self.env.company.currency_id,
    )
    amunet_monto = fields.Monetary(
        string='Importe a pagar',
        currency_field='amunet_currency_id',
        tracking=True,
        groups=GRUPO_MONTO,
        help='Importe total de la compra. Solo lo ve el area de compras.',
    )
    amunet_monto_visible = fields.Char(
        string='Importe',
        compute='_compute_amunet_monto_visible',
        help='El importe, mostrado unicamente a quien le corresponde verlo.',
    )

    amunet_banco = fields.Char(string='Banco', tracking=True)
    amunet_clabe = fields.Char(string='CLABE interbancaria', tracking=True)
    amunet_titular = fields.Char(string='Titular de la cuenta', tracking=True)
    amunet_referencia_pago = fields.Char(string='Referencia de pago', tracking=True)

    @api.depends_context('uid')
    @api.depends('amunet_currency_id')
    def _compute_amunet_monto_visible(self):
        puede_todo = (
            self.env.su
            or self.env.user.has_group(GRUPO_MONTO)
            or self.env.user.has_group('amunet_material_request.group_material_manager')
        )
        for req in self:
            aprobador = req.sudo().requester_id.amunet_material_head_id
            autorizado = puede_todo or bool(aprobador and aprobador.id == self.env.uid)
            monto = req.sudo().amunet_monto if autorizado else 0.0
            if not autorizado or not monto:
                req.amunet_monto_visible = False
                continue
            req.amunet_monto_visible = '%s %s' % (
                req.sudo().amunet_currency_id.symbol or '$',
                '{:,.2f}'.format(monto),
            )

    @api.constrains('amunet_clabe')
    def _check_clabe(self):
        for req in self:
            if not req.amunet_clabe:
                continue
            limpia = req.amunet_clabe.replace(' ', '').replace('-', '')
            if not (limpia.isdigit() and len(limpia) == 18):
                raise ValidationError(_(
                    'La CLABE debe tener exactamente 18 digitos; se capturaron %s. '
                    'Revisa que no falte ni sobre un numero: una CLABE mal escrita '
                    'manda el dinero a otra cuenta.'
                ) % len(limpia))

    @api.constrains('amunet_forma_pago', 'amunet_clabe', 'amunet_titular', 'amunet_banco', 'state')
    def _check_datos_transferencia(self):
        for req in self:
            if req.amunet_forma_pago != 'transferencia' or req.state == 'draft':
                continue
            faltan = []
            if not req.amunet_clabe:
                faltan.append('CLABE')
            if not req.amunet_titular:
                faltan.append('titular de la cuenta')
            if not req.amunet_banco:
                faltan.append('banco')
            if faltan:
                raise ValidationError(_(
                    'Para pagar por transferencia falta capturar: %s.\n\n'
                    'Sin esos datos no se puede pedir el pago.'
                ) % ', '.join(faltan))
