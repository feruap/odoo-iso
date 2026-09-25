# -*- coding: utf-8 -*-
"""Seguimiento de la orden de compra: via, pago y llegada real.

NADA DE ESTO TOCA CONTABILIDAD. La contabilidad de Amunet vive fuera de
Odoo; aqui solo se anota, de forma estructurada, en que va el pago y
cuando dijo el proveedor que llega. No se crea ni se lee account.move ni
account.payment.

Por que un campo de llegada aparte de date_planned: date_planned se pone
al crear la orden y nadie lo vuelve a tocar. P00214 decia 18-ago y llego
el 17-sep; P00213 decia 7-ago y llego el 28-ago. `amunet_eta` es la fecha
que confirma el proveedor y lleva tracking, asi que cada vez que se
recorre queda el rastro de quien y cuando lo movio.
"""

from odoo import _, api, fields, models
from odoo.exceptions import AccessError

from .urgencia import URGENCIA_PESO, URGENCIA_SELECTION

GRUPO_PAGOS = 'amunet_compras_general.group_compras_pagos'

# Sugerencia de via por urgencia. Es texto, no automatismo: quien paga el
# flete es Compras y la decision es suya.
SUGERENCIA_VIA = {
    'linea_detenida': 'aereo',
    'urge': 'aereo',
}


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # -- de donde viene la orden -----------------------------------------
    amunet_solicitud_compra_ids = fields.One2many(
        'amunet.solicitud.compra', 'purchase_order_id',
        string='Solicitudes del Marketplace',
        help='Las solicitudes internas que originaron esta orden.',
    )

    # -- embarque ---------------------------------------------------------
    amunet_via_embarque = fields.Selection(
        selection=[
            ('aereo', 'Aereo'),
            ('maritimo', 'Maritimo'),
            ('terrestre', 'Terrestre'),
            ('mensajeria', 'Mensajeria'),
        ],
        string='Via de embarque',
        tracking=True,
        help='Como viene la mercancia. Lo captura Compras.',
    )
    amunet_via_sugerida = fields.Char(
        string='Sugerencia de via',
        compute='_compute_amunet_via_sugerida',
        help='Solo una sugerencia, a partir de la urgencia de las solicitudes '
             'ligadas. No llena ni cambia la via de embarque: el costo del '
             'flete lo decide Compras.',
    )
    amunet_urgencia_maxima = fields.Selection(
        selection=URGENCIA_SELECTION,
        string='Urgencia de origen',
        compute='_compute_amunet_via_sugerida',
        help='La urgencia mas alta de las solicitudes ligadas.',
    )

    # -- pago (nota de seguimiento, NO contabilidad) ----------------------
    amunet_estado_pago = fields.Selection(
        selection=[
            ('pendiente', 'Pendiente'),
            ('anticipo', 'Anticipo pagado'),
            ('pagado', 'Pagado'),
        ],
        string='Estado de pago',
        default='pendiente',
        tracking=True,
        help='Nota de seguimiento. No genera ningun asiento: la contabilidad '
             'de Amunet no vive en Odoo.',
    )
    amunet_pago_fecha = fields.Date(
        string='Fecha de pago', tracking=True)
    amunet_pago_referencia = fields.Char(
        string='Referencia de pago', tracking=True,
        help='Folio de la transferencia o del cargo, para poder cruzarlo '
             'contra el estado de cuenta.')

    # -- llegada ----------------------------------------------------------
    amunet_eta = fields.Date(
        string='Llegada estimada (confirmada por el proveedor)',
        tracking=True,
        help='La fecha que confirmo el proveedor, y que se recorre cuantas '
             'veces haga falta. Es distinta de "Fecha planeada", que se pone '
             'al crear la orden y casi nunca se actualiza.',
    )

    @api.depends('amunet_solicitud_compra_ids.amunet_urgencia')
    def _compute_amunet_via_sugerida(self):
        etiquetas = dict(URGENCIA_SELECTION)
        for orden in self:
            urgencias = orden.amunet_solicitud_compra_ids.mapped('amunet_urgencia')
            peor = 'normal'
            for u in urgencias:
                if URGENCIA_PESO.get(u, 0) > URGENCIA_PESO.get(peor, 0):
                    peor = u
            orden.amunet_urgencia_maxima = peor
            via = SUGERENCIA_VIA.get(peor)
            if not via:
                orden.amunet_via_sugerida = False
                continue
            orden.amunet_via_sugerida = _(
                "Esta compra viene de una solicitud marcada '%s': se sugiere %s"
            ) % (etiquetas.get(peor, peor), via)

    # -- candado de los campos de pago ------------------------------------
    # Los campos NO llevan groups= a proposito: todos deben poder VER en que
    # va el pago; lo que se restringe es escribirlo. El candado va en write()
    # para que valga tambien por RPC o por importacion, no solo en la vista.
    _AMUNET_CAMPOS_PAGO = (
        'amunet_estado_pago', 'amunet_pago_fecha', 'amunet_pago_referencia')

    amunet_puede_capturar_pagos = fields.Boolean(
        string='Puede capturar pagos',
        compute='_compute_amunet_puede_capturar_pagos',
        help='Tecnico: la vista lo usa para dejar los campos de pago de solo '
             'lectura a quien no esta en el grupo.',
    )

    @api.depends_context('uid')
    def _compute_amunet_puede_capturar_pagos(self):
        permitido = self._amunet_puede_capturar_pagos()
        for orden in self:
            orden.amunet_puede_capturar_pagos = permitido

    def _amunet_puede_capturar_pagos(self):
        return self.env.su or self.env.user.has_group(GRUPO_PAGOS)

    def write(self, vals):
        tocados = [f for f in self._AMUNET_CAMPOS_PAGO if f in vals]
        if tocados and not self._amunet_puede_capturar_pagos():
            raise AccessError(_(
                'Solo el grupo "Compras / Captura de pagos" puede capturar los '
                'datos de pago de una orden de compra. Campos bloqueados: %s.'
            ) % ', '.join(tocados))
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            tocados = [f for f in self._AMUNET_CAMPOS_PAGO
                       if vals.get(f) not in (None, False)]
            # 'pendiente' es el valor por omision: dejarlo pasar no es capturar.
            if 'amunet_estado_pago' in tocados and vals.get('amunet_estado_pago') == 'pendiente':
                tocados.remove('amunet_estado_pago')
            if tocados and not self._amunet_puede_capturar_pagos():
                raise AccessError(_(
                    'Solo el grupo "Compras / Captura de pagos" puede capturar '
                    'los datos de pago de una orden de compra. Campos '
                    'bloqueados: %s.') % ', '.join(tocados))
        ordenes = super().create(vals_list)
        ordenes._amunet_amarrar_solicitud()
        return ordenes

    def _amunet_amarrar_solicitud(self):
        """Deja puesto purchase_order_id en la solicitud que origino la orden.

        La accion "Generar orden de compra" (amunet_compras_enlace) es un
        server action en XML que escribe `origin` con el folio de la solicitud
        pero no regresa a amarrarla. En vez de reescribir ese XML -- que
        tambien lo usan las solicitudes de material -- se cierra el circulo
        aqui, al crear la orden: sirve para los dos caminos y para cualquier
        otro que respete `origin`.

        sudo() es necesario: quien genera la orden de compra es el area de
        compras, que no tiene por que tener permiso de escritura sobre la
        solicitud interna de otra area.
        """
        Solicitud = self.env['amunet.solicitud.compra'].sudo()
        Material = self.env['amunet.material.request'].sudo()
        for orden in self:
            origen = (orden.origin or '').strip()
            if not origen:
                continue
            sol = Solicitud.search(
                [('name', '=', origen), ('purchase_order_id', '=', False)],
                limit=1)
            if not sol:
                # La accion actual corre sobre solicitudes de MATERIAL: si esa
                # solicitud tiene una de compra derivada, es esa la que se amarra.
                mat = Material.search([('name', '=', origen)], limit=1)
                if mat:
                    sol = Solicitud.search(
                        [('amunet_material_request_id', '=', mat.id),
                         ('purchase_order_id', '=', False)], limit=1)
            if sol:
                sol.write({'purchase_order_id': orden.id})
                sol.message_post(body=_(
                    'Se ligo con la orden de compra <b>%s</b>.') % orden.name)
