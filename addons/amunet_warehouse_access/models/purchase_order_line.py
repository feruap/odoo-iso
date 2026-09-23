# -*- coding: utf-8 -*-
# Descripcion de la linea de Orden de Compra.
#
# La OC es un documento PARA EL PROVEEDOR: debe llevar SU codigo y SU nombre
# (product.supplierinfo), en su idioma. Hasta 19.0.1.1.0 este modulo anteponia
# la clave interna de Amunet ("[SPHMC64] Hoja Maestra ...") y dejaba la del
# proveedor como "Ref. proveedor" en una segunda linea; Tongzhou y Fapon
# recibian ordenes con claves que no reconocen y texto en espanol. Fernando lo
# marco como error del sistema el 23-sep-2026.
#
# Regla actual:
#   - Si hay supplierinfo del proveedor con codigo o nombre -> "[codigo] nombre"
#     del proveedor. Nada interno.
#   - Si no hay supplierinfo -> "[clave] nombre" interno (no hay otra cosa).
#   - La clave interna sigue visible en Odoo en la columna Producto de la linea;
#     solo se quita del TEXTO que se imprime.
#
# NOTA: solo afecta el texto de la descripcion. No toca precios ni su
# visibilidad (amunet_price_visibility).
from odoo import models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _amunet_supplierinfo(self, product):
        self.ensure_one()
        partner = self.order_id.partner_id or self.partner_id
        if not partner:
            return self.env['product.supplierinfo']
        sellers = product.seller_ids.filtered(
            lambda s: s.partner_id.commercial_partner_id == partner.commercial_partner_id
            and (not s.product_id or s.product_id == product))
        con_dato = sellers.filtered(lambda s: s.product_code or s.product_name)
        return (con_dato or sellers)[:1]

    def _get_product_purchase_description(self, product_lang):
        self.ensure_one()
        si = self._amunet_supplierinfo(product_lang)
        if si and (si.product_code or si.product_name):
            nombre = si.product_name or product_lang.name or ''
            name = '[%s] %s' % (si.product_code, nombre) if si.product_code else nombre
        else:
            name = product_lang.name or ''
            if product_lang.default_code:
                name = '[%s] %s' % (product_lang.default_code, name)
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase
        return name
