# -*- coding: utf-8 -*-
"""Mantiene al dia el bloqueo que muestra el tablero de Calidad.

El problema que resuelve: `tablero_mo_count` es un campo CALCULADO Y GUARDADO
cuyas dependencias son solo campos del propio analisis
(`product_id`, `lot_id`, `state`). Por eso, cuando se crea una orden de
produccion que espera un material, los analisis de ese material NO se enteran:
el analisis ya existia, la orden llego despues, y nadie le aviso.

Efecto real (2026-09-01): la orden 0926/01/ZKC esperaba las hojas de Zika
SPHMC61 y SPHMC62, y sus analisis seguian marcados "normal" en el tablero
mientras la produccion estaba detenida.

No se puede expresar con @api.depends "cualquier orden que consuma este
producto", asi que se avisa desde el otro lado: cuando una orden nace o cambia
de estado, se recalculan los analisis abiertos de sus insumos.
"""

from odoo import api, models

# Estados en los que una orden cuenta como "esperando material"
MO_RELEVANTES = ('draft', 'confirmed', 'progress', 'to_close', 'done', 'cancel')


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _tablero_refrescar_checks(self):
        """Recalcula el bloqueo de los analisis abiertos de los insumos."""
        productos = self.mapped('move_raw_ids.product_id')
        if not productos:
            return
        checks = self.env['amunet.quality.check'].sudo().search([
            ('product_id', 'in', productos.ids),
            ('state', 'not in', ('done', 'cancel')),
        ])
        if checks:
            checks._compute_tablero_bloqueo()
            checks._compute_tablero_prioridad()
            checks._compute_tablero_orden()

    @api.model_create_multi
    def create(self, vals_list):
        ordenes = super().create(vals_list)
        ordenes._tablero_refrescar_checks()
        return ordenes

    def write(self, vals):
        res = super().write(vals)
        # El estado decide si la orden cuenta como detenida; los insumos deciden
        # a que analisis afecta. Cualquiera de los dos obliga a recalcular.
        if 'state' in vals or 'move_raw_ids' in vals:
            self._tablero_refrescar_checks()
        return res
