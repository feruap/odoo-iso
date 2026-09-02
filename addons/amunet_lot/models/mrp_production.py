# -*- coding: utf-8 -*-

from odoo import fields, models


class MrpProduction(models.Model):
    """Sella la fecha de fabricacion en el lote que produce la orden.

    Hasta ahora la fecha de fabricacion solo se capturaba a mano en la pantalla
    de recepcion, pensada para material de proveedor. Los lotes que fabricamos
    nosotros nacian sin ella, aunque el sistema si sabe cuando se fabricaron: es
    la fecha en que se termino su orden.

    Se implementa aqui y no en amunet_production porque ese modulo diverge entre
    staging y produccion; amunet_lot es identico en ambos y es el dueno del
    campo.
    """
    _inherit = 'mrp.production'

    def button_mark_done(self):
        res = super().button_mark_done()
        # button_mark_done puede devolver un asistente (aviso de consumo, backorder)
        # sin haber terminado la orden. Solo sellamos las que si quedaron hechas.
        self.filtered(lambda o: o.state == 'done')._amunet_sellar_fecha_fabricacion()
        return res

    def _amunet_sellar_fecha_fabricacion(self):
        """Escribe la fecha de fabricacion en los lotes producidos que no la traen.

        Nunca sobrescribe un dato existente: si alguien la capturo a mano, esa
        gana. El campo lleva tracking, asi que el cambio queda en el historial
        del lote.

        Los lotes YA LIBERADOS se saltan a proposito. amunet_quality prohibe
        tocar campos criticos de un lote liberado: cambiar ese expediente exige
        un reanalisis o una desviacion/CAPA. Saltarlos aqui respeta ese control
        y, sobre todo, evita que la excepcion impida cerrar la orden.
        """
        for orden in self:
            fecha = (orden.date_finished or fields.Datetime.now()).date()
            lotes = orden.move_finished_ids.move_line_ids.lot_id
            faltantes = lotes.filtered(
                lambda l: not l.manufacturing_date and not self._amunet_lote_liberado(l))
            if faltantes:
                faltantes.sudo().write({'manufacturing_date': fecha})

    @staticmethod
    def _amunet_lote_liberado(lote):
        # amunet_quality puede no estar instalado: no se asume el campo.
        if 'amunet_lot_release_state' not in lote._fields:
            return False
        return lote.amunet_lot_release_state == 'released'
