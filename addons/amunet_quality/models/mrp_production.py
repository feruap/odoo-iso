# -*- coding: utf-8 -*-
"""El analisis de PRODUCTO TERMINADO se cierra al cerrar la orden.

El cierre del analisis estaba pensado para INSUMOS: llega material del proveedor,
Calidad lo analiza, Almacen valida la recepcion de lo aprobado y ahi el analisis
pasa a 'done' (ver `_action_warehouse_reception_done`).

El producto terminado no viene de un proveedor: nace de una orden. Almacen de
Materia Prima no tiene nada que validar, asi que esos analisis se quedaban
esperando a alguien a quien no le correspondia, para siempre. Al 23-sep-2026
habia 6 asi, y en 5 la orden ya estaba CERRADA: el trabajo hecho y el analisis
abierto en "Mi trabajo Calidad".

Regla de Mery (23-sep-2026): en producto terminado el cierre lo marca la ORDEN.

  - al cerrar la orden, los analisis de PT que Calidad YA TERMINO pasan a 'done'
  - si Calidad NO termino, la orden NO se cierra: se bloquea con el motivo

Lo segundo es a proposito. Cerrar un analisis a medias lo haria desaparecer del
tablero de Calidad sin que nadie lo hiciera, y es el registro que respalda un
producto medico. Bloquear es el mismo criterio que el resto de los candados de la
casa.
"""

from odoo import _, models
from odoo.exceptions import UserError

# Calidad ya acabo: solo falta el cierre administrativo.
ESTADOS_TERMINADOS = ('awaiting_reception', 'pending')
# Calidad tiene trabajo sin hacer: la orden no debe cerrar.
ESTADOS_PENDIENTES = ('draft', 'in_progress')


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _amunet_pt_quality_checks(self):
        """Analisis de PRODUCTO TERMINADO de esta orden."""
        self.ensure_one()
        checks = self.env['amunet.quality.check'].sudo().search([
            ('amunet_production_id', '=', self.id),
        ])
        return checks.filtered(
            lambda c: (c.product_id.categ_id.complete_name or '').startswith(
                'Producto terminado'))

    def _amunet_check_pt_quality_done(self):
        """Impide cerrar la orden si su analisis de PT no esta terminado."""
        for rec in self:
            pendientes = rec._amunet_pt_quality_checks().filtered(
                lambda c: c.state in ESTADOS_PENDIENTES)
            if not pendientes:
                continue
            detalle = '\n'.join(
                '  - %s: %s' % (c.name, dict(
                    c._fields['state'].selection).get(c.state, c.state))
                for c in pendientes)
            raise UserError(_(
                'Esta orden no se puede cerrar todavía: Calidad no ha terminado '
                'el análisis del producto terminado.\n\n%(detalle)s\n\n'
                'En producto terminado el análisis se cierra al cerrar la orden, '
                'así que si la orden cierra antes, ese análisis desaparece del '
                'tablero de Calidad sin que nadie lo haya hecho. Y es el '
                'registro que respalda el lote.\n\n'
                'Qué hacer: pídele a Calidad que termine el análisis, o si ya '
                'está hecho en papel, que lo capture y lo autorice.'
            ) % {'detalle': detalle})

    def _amunet_close_pt_quality_checks(self):
        """Cierra los analisis de PT cuya parte de Calidad ya esta hecha.

        NO cambia el dictamen: `global_result` conserva si el lote paso o no. Lo
        unico que se asienta es que el tramite termino.
        """
        for rec in self:
            for check in rec._amunet_pt_quality_checks().filtered(
                    lambda c: c.state in ESTADOS_TERMINADOS):
                check.write({
                    'state': 'done',
                    'change_reason': _(
                        'Cerrado al cerrar la orden de fabricación %s. En '
                        'producto terminado el cierre lo marca la orden, no la '
                        'recepción de Almacén.') % rec.name,
                })
                check.message_post(body=_(
                    'Análisis cerrado automáticamente al cerrar la orden '
                    '%(orden)s. Resultado del análisis: %(res)s. El cierre no '
                    'cambia el dictamen, solo asienta que el trámite terminó.'
                ) % {
                    'orden': rec.name,
                    'res': check.global_result or 'sin resultado registrado',
                })

    def button_mark_done(self):
        self._amunet_check_pt_quality_done()
        res = super().button_mark_done()
        # despues del super: solo se cierran los analisis de las ordenes que de
        # verdad quedaron cerradas
        self.filtered(lambda r: r.state == 'done')._amunet_close_pt_quality_checks()
        return res
