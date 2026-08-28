# -*- coding: utf-8 -*-
from odoo import models


class StockLot(models.Model):
    """La cuarentena no es un anaquel.

    El semaforo de caducidad mira donde tiene existencia cada lote para decidir
    si esta fuera de su lugar. Sin esto, un lote devuelto que espera dictamen se
    veria como si estuviera en el anaquel normal y el sistema pediria moverlo,
    cuando lo correcto es que nadie lo toque hasta que calidad lo revise.

    Para el semaforo, lo que esta en cuarentena no esta en ningun anaquel.
    """
    _inherit = 'stock.lot'

    def _amunet_donde_esta(self):
        self.ensure_one()
        cuarentena = self.env.ref('amunet_devoluciones.location_devoluciones',
                                  raise_if_not_found=False)
        if not cuarentena:
            return super()._amunet_donde_esta()

        quants = self.quant_ids.filtered(
            lambda q: q.location_id.usage == 'internal' and q.quantity > 0)
        fuera = quants.filtered(lambda q: q.location_id != cuarentena)
        if quants and not fuera:
            return 'sin_stock'      # todo lo que hay esta detenido, no en un anaquel
        return super()._amunet_donde_esta()
