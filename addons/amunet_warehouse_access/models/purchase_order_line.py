# -*- coding: utf-8 -*-
# Descripcion de la linea de Orden de Compra: mostrar SIEMPRE primero el
# nombre y clave INTERNOS de Amunet, y debajo la referencia del proveedor.
#
# Odoo estandar, cuando la linea se arma con el proveedor en contexto, usa el
# nombre/codigo del proveedor (product.supplierinfo) y esconde el nuestro, lo
# que confunde a quien hace la compra. Aqui se antepone lo nuestro.
#
# NOTA: esto solo afecta el TEXTO de la descripcion. No toca precios ni su
# visibilidad (la restriccion de precios sigue intacta en amunet_price_visibility).
from odoo import models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _get_product_purchase_description(self, product_lang):
        self.ensure_one()
        # Nombre INTERNO (clave + nombre), sin la sustitucion por proveedor.
        # product_lang.name / .default_code son los nuestros; solo display_name
        # aplica la sustitucion del proveedor.
        interno = product_lang.name or ''
        if product_lang.default_code:
            interno = '[%s] %s' % (product_lang.default_code, interno)
        name = interno
        # Referencia del proveedor (para que el proveedor reconozca el producto).
        ref_prov = product_lang.display_name
        if ref_prov and ref_prov != interno:
            name += '\nRef. proveedor: %s' % ref_prov
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase
        return name
