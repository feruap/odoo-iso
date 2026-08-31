# -*- coding: utf-8 -*-

from odoo import models


class MrpProduction(models.Model):
    """Cierre de orden de fabricación (enganche documental).

    Cambio de diseño (RECEPCIÓN-céntrico): al cerrar la MO ya NO se publica a
    la tienda. El producto terminado queda para que Calidad lo LIBERE y luego
    el almacén de venta ACEPTE su recepción (``amunet.woo.reception``), que es
    lo que dispara la publicación. Por eso ya no se sobreescribe
    ``button_mark_done``: no debe interferir con el cierre de producción ni
    publicar existencias que aún no han sido recibidas por el almacén.
    """

    _inherit = "mrp.production"
