# -*- coding: utf-8 -*-
"""Filtro de producto por ETAPA DE LINEA LARGA.

El campo Producto ya se filtraba por LINEA de produccion (route_type): corta
ofrece terminados y soluciones ofrece la categoria "solucion". Pero los
conjugados viven en esa misma categoria, asi que una orden de conjugado ofrecia
TODAS las soluciones -- casi cien -- y no las 29 que aplican.

Aqui cada producto declara a que ETAPA de la linea larga pertenece (soluciones,
conjugados, inyeccion, laminado) y el campo Producto se acota a la etapa
elegida. Cuando la orden no tiene etapa, se conserva el filtro por linea de
siempre.
"""

from odoo import api, fields, models

ETAPAS = [
    ('soluciones', 'Soluciones'),
    ('conjugados', 'Conjugados'),
    # Pretratado y corte: las almohadillas SPALMA. Se sumergen en solucion de
    # pretratamiento, se secan 4 h a 37 C y se cortan al ancho de cada una.
    # Faltaba en la lista, asi que sus ordenes no se podian clasificar y las 13
    # almohadillas no aparecian al elegir producto (Mery, 22-sep-2026).
    ('pretratado', 'Pretratado y corte'),
    ('inyeccion', 'Inyección'),
    ('laminado', 'Laminado'),
    # Llenado de viales: va de la solucion de corrimiento A GRANEL al vial lleno.
    # Es el eslabon entre Soluciones y el producto terminado que la consume.
    # No lleva etiquetado -- eso pasa hasta Acondicionado. Mery, 24-sep-2026.
    ('llenado', 'Llenado de Viales'),
]


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    amunet_etapa_ll = fields.Selection(
        selection=ETAPAS, string='Etapa de línea larga', index=True,
        help='Etapa de la linea larga en la que se fabrica este producto. '
             'Filtra el campo Producto de las ordenes: una orden de Conjugados '
             'solo ofrece productos de conjugados. Vacio = no es de linea larga.')


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # Para la vista: la caducidad de un vial NO se captura, se hereda del
    # granel que lo llena. Sin este campo la casilla 'Caducidad' salia
    # editable -- solo se bloquea para soluciones, y un vial es
    # 'Semiterminado / Buffer' -- asi que el operador podia escribir una fecha
    # que el sistema despues ignoraba. Una casilla que acepta lo que no
    # respeta es peor que una bloqueada.
    amunet_es_llenado_vial = fields.Boolean(
        string='Es llenado de viales',
        compute='_compute_amunet_es_llenado_vial',
        help='Verdadero cuando el producto de la orden es de la etapa '
             'Llenado de Viales.')

    @api.depends('product_id')
    def _compute_amunet_es_llenado_vial(self):
        # Delega en amunet_production para que el criterio viva en UN solo sitio:
        # ahi estan el destino, la caducidad heredada y el formato de lote.
        for rec in self:
            rec.amunet_es_llenado_vial = rec._amunet_es_etapa_llenado()

    @api.onchange('amunet_sublinea')
    def _amunet_onchange_sublinea_limpia_producto(self):
        """Si el producto ya elegido no pertenece a la etapa, se limpia.

        Evita el caso silencioso de cambiar la etapa y dejar un producto que no
        corresponde: la orden quedaria clasificada en una etapa con un producto
        de otra.
        """
        for rec in self:
            if not rec.amunet_sublinea or not rec.product_id:
                continue
            if rec.product_id.product_tmpl_id.amunet_etapa_ll != rec.amunet_sublinea:
                rec.product_id = False

    @api.onchange('product_id')
    def _amunet_onchange_product_sublinea(self):
        """La etapa sigue al producto.

        Los conjugados viven en la categoria 'Soluciones de trabajo', asi que
        la orden nacia clasificada como Soluciones y el filtro 'Conjugados' de
        la busqueda no mostraba ninguna. Reportado por Mery, 18-sep-2026.
        """
        for rec in self:
            etapa = rec.product_id.product_tmpl_id.amunet_etapa_ll
            if etapa:
                rec.amunet_sublinea = etapa
