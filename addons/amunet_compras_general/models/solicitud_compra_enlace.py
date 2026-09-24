# -*- coding: utf-8 -*-
"""Amarre manual entre la solicitud y la orden de compra.

El campo nacio readonly en amunet_marketplace, pensando en que siempre lo
pondria el sistema. En la practica hay ordenes creadas sueltas (P00226 y
P00227 se crearon por script) que nadie puede ligar despues. Aqui se abre
a captura, sin quitar la liga automatica que hace purchase.order.create.
"""

from odoo import api, fields, models


class AmunetSolicitudCompra(models.Model):
    _inherit = 'amunet.solicitud.compra'

    purchase_order_id = fields.Many2one(
        readonly=False,
        help='La orden que genero esta solicitud. Se pone sola al generar la '
             'orden desde la solicitud, y se puede capturar a mano para '
             'amarrar ordenes que se crearon por fuera.',
    )


    # -- espejo de la orden, para que el solicitante vea en que va --------
    # Son campos calculados y no related: el solicitante de un area no tiene
    # permiso de lectura sobre purchase.order, y un related tronaria al
    # abrir su propia lista. sudo() aqui solo lee tres datos de seguimiento
    # de SU orden; el monto no se toca y sigue protegido por su propio grupo.
    amunet_oc_estado_pago = fields.Selection(
        selection=[
            ('pendiente', 'Pendiente'),
            ('anticipo', 'Anticipo pagado'),
            ('pagado', 'Pagado'),
        ],
        string='Estado de pago de la orden',
        compute='_compute_amunet_datos_orden', store=True)
    amunet_oc_via_embarque = fields.Selection(
        selection=[
            ('aereo', 'Aereo'),
            ('maritimo', 'Maritimo'),
            ('terrestre', 'Terrestre'),
            ('mensajeria', 'Mensajeria'),
        ],
        string='Via de embarque',
        compute='_compute_amunet_datos_orden', store=True)
    amunet_oc_eta = fields.Date(
        string='Llegada estimada',
        compute='_compute_amunet_datos_orden', store=True)

    # store=True para poder AGRUPAR por estado de pago en la vista de
    # seguimiento: Odoo no agrupa por un calculado que no esta guardado.
    @api.depends('purchase_order_id.amunet_estado_pago',
                 'purchase_order_id.amunet_via_embarque',
                 'purchase_order_id.amunet_eta')
    def _compute_amunet_datos_orden(self):
        for req in self:
            oc = req.purchase_order_id.sudo()
            req.amunet_oc_estado_pago = oc.amunet_estado_pago if oc else False
            req.amunet_oc_via_embarque = oc.amunet_via_embarque if oc else False
            req.amunet_oc_eta = oc.amunet_eta if oc else False

    def action_amunet_abrir_solicitud(self):
        """Abre la solicitud desde el recuadro de la orden de compra."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': 'amunet.solicitud.compra',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
