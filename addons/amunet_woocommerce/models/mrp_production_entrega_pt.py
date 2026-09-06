# -*- coding: utf-8 -*-
"""El boton "Entrega de PT" en la orden de fabricacion.

Archivo aparte a proposito: mrp_production.py de este modulo es de otro frente
(publicacion de lotes a la tienda) y meter esto ahi mezclaria dos temas que se
tocan en momentos distintos.
"""

from odoo import _, fields, models
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    amunet_entrega_pt_disponible = fields.Boolean(
        string='Se puede entregar a PT',
        compute='_compute_amunet_entrega_pt_disponible',
        help='Uso de la vista: decide si se muestra el boton "Entrega de PT".')

    def _compute_amunet_entrega_pt_disponible(self):
        """El boton aparece cuando arranco la primera actividad de la ruta.

        UNA sola condicion, que es la que se pidio. Se probo tambien exigir que
        hubiera piezas pendientes y se DESCARTO: un boton ausente no explica
        nada -quien lo busca no sabe si falta material, si le falta permiso o si
        el sistema fallo-. El candado de "no se entrega lo que no existe" vive
        donde debe, en la validacion al confirmar, que avisa con su motivo.
        """
        for mo in self:
            mo.amunet_entrega_pt_disponible = (
                mo.state != 'cancel'
                and any(wo.state in ('progress', 'done')
                        for wo in mo.workorder_ids))

    def action_amunet_entrega_pt(self):
        """Un solo boton: la cantidad y si es parcial o total se define adentro."""
        self.ensure_one()
        if not self.env.user.has_group(
                'amunet_production.group_production_operator'):
            raise UserError(_(
                'Solo Produccion puede entregar material al almacen de '
                'producto terminado.'))
        return self.env['amunet.entrega.pt.wizard'].abrir_para(self)
