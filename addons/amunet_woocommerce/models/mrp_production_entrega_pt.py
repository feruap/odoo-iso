# -*- coding: utf-8 -*-
"""El boton "Entrega de PT" en la orden de fabricacion.

Archivo aparte a proposito: mrp_production.py de este modulo es de otro frente
(publicacion de lotes a la tienda) y meter esto ahi mezclaria dos temas que se
tocan en momentos distintos.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    amunet_entrega_pt_disponible = fields.Boolean(
        string='Se puede entregar a PT',
        compute='_compute_amunet_entrega_pt_disponible',
        help='Uso de la vista: decide si se muestra el boton "Entrega de PT".')

    @api.depends('state', 'workorder_ids.state', 'quality_analysis_status',
                 'amunet_qc_check_ids.state', 'amunet_sys_req_qc',
                 'amunet_es_desarrollo')
    def _compute_amunet_entrega_pt_disponible(self):
        """El boton aparece cuando el producto YA ESTA LIBERADO por Calidad.

        Antes bastaba con que hubiera arrancado una actividad de la ruta. Eso
        permitia entregar a PT producto que Calidad todavia no liberaba, y la
        entrega es justo el acto que lo vuelve vendible. Cambio pedido por Mery
        (09-sep-2026): la entrega va DESPUES de la liberacion.

        Liberado, parcial o total, es un analisis de esta orden en
        'awaiting_reception' (aprobado, pendiente de recibir en almacen) o
        'done' (finalizado). Un analisis parcial habilita la entrega de la
        parte liberada: la cantidad se define adentro del asistente.

        Nota de diseno: hay una decision previa en contra de esconder este
        boton -un boton ausente no explica por que no esta-. Se conserva la
        parte que si comunica: el estado del analisis es visible en la orden, y
        el boton "Solicitar analisis" queda a la vista cuando falta pedirlo.
        """
        for mo in self:
            # Producto que por diseno no lleva analisis: no hay nada que
            # liberar, y exigirlo dejaria la entrega bloqueada para siempre.
            sin_analisis = (not mo.amunet_sys_req_qc) or mo.amunet_es_desarrollo
            liberado = any(
                c.state in ('awaiting_reception', 'done')
                for c in mo.amunet_qc_check_ids)
            mo.amunet_entrega_pt_disponible = (
                mo.state != 'cancel'
                and any(wo.state in ('progress', 'done')
                        for wo in mo.workorder_ids)
                # Un lote RECHAZADO no se entrega: se da de baja a APT/Rechazo.
                and mo.quality_analysis_status != 'rejected'
                and (sin_analisis or liberado))

    def action_amunet_entrega_pt(self):
        """Un solo boton: la cantidad y si es parcial o total se define adentro."""
        self.ensure_one()
        if not self.env.user.has_group(
                'amunet_production.group_production_operator'):
            raise UserError(_(
                'Solo Produccion puede entregar material al almacen de '
                'producto terminado.'))
        return self.env['amunet.entrega.pt.wizard'].abrir_para(self)
