# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Plan de produccion sugerido',
    'summary': 'Sustituto libre del Plan Maestro (mrp_mps, Enterprise): demanda historica + inventario PT + disponibilidad de materia prima segun BoM.',
    'description': """
Plan de produccion sugerido
===========================

Odoo Community no incluye el Plan Maestro de Produccion (`mrp_mps` es Enterprise).
Este modulo lo sustituye y ademas hace algo que el MPS de Odoo NO hace: valida la
disponibilidad de materia prima explotando la BoM antes de sugerir la orden.

Como calcula cada linea
-----------------------
1. DEMANDA. Se toma de una de tres fuentes (configurable por plan):
   - Tendencia WooCommerce (`amunet.woo.sales.trend`): piezas vendidas. SIN precios.
   - Pedidos de venta (`sale.order.line`) confirmados en la ventana.
   - Salidas de almacen (`stock.move` hechos hacia cliente) en la ventana.
   demanda_diaria = piezas de la ventana / dias de la ventana
   demanda_horizonte = demanda_diaria * dias_horizonte

2. OFERTA YA EXISTENTE:
   - stock_pt: existencia disponible (libre de reservas) del producto terminado.
   - stock_pt_liberado: solo lotes liberados por Calidad, si el modulo de lotes
     esta instalado.
   - en_produccion: piezas en ordenes de fabricacion abiertas.

3. SUGERIDO = demanda_horizonte + stock_seguridad - stock_pt - en_produccion
   (nunca negativo). El stock de seguridad se expresa en dias de demanda.

4. RESTRICCION DE MATERIA PRIMA. Se explota la BoM por la cantidad sugerida y por
   cada componente se compara requerido contra disponible libre.
   cobertura = min(disponible / requerido) acotado a 1.
   a_producir = sugerido * cobertura (redondeado hacia abajo).
   Los componentes que no alcanzan se listan como faltantes, con el numero de
   piezas que bloquean. Esa lista es la orden de compra que hay que levantar.

5. Boton para crear las ordenes de fabricacion en BORRADOR. Nunca confirma nada
   por su cuenta: la decision sigue siendo humana y queda trazada.

Notas
-----
- Todo se maneja en PIEZAS. Las cajas son presentaciones
  (`amunet.packaging.presentation`), no inventario propio.
- El plan no lee ni muestra un solo importe. Es compatible con la politica de
  amunet_price_visibility / amunet_sale_confidential.
    """,
    'author': 'Amunet',
    'category': 'Manufacturing',
    'version': '19.0.4.0.0',
    'depends': ['mrp', 'stock', 'product', 'purchase'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/production_plan_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
