# -*- coding: utf-8 -*-
"""Cuatro decimales en las cantidades.

Con 2 decimales Odoo no podia expresar 333 ml de un producto que se lleva en
LITROS: 0.333 L se redondeaba a 0.33 (330 ml), y los 3 ml sobrantes se iban a
un segundo lote. De ahi salia el lote partido que chocaba con el candado ISO de
un lote por componente. Decision de Mery, 22-sep-2026.

OJO: en Odoo 19 el redondeo NO es por unidad. `uom.uom.rounding` es un campo
CALCULADO (store=False) que sale de una sola configuracion global: la precision
decimal 'Product Unit'. Por eso esto no se puede limitar a L, ml y g: o son 4
decimales para todas las unidades, o para ninguna.

Cambia solo:
    decimal.precision 'Product Unit'   2 -> 4

NO toca 'Product Price' (los precios no entran) ni 'Stock Weight' (es el peso
para envios, nada que ver con fabricar soluciones).

Correr con:
  /opt/odoo/scripts/run_correction.sh production precision_4_decimales_2026-09-22.py
"""

d = env['decimal.precision'].search([('name', '=', 'Product Unit')], limit=1)
if not d:
    print('No existe la precision "Product Unit". Revisar a mano.')
else:
    print('Product Unit: %s -> 4' % d.digits)
    if d.digits < 4:
        d.sudo().digits = 4

print('\nsin tocar:')
for nombre in ('Product Price', 'Stock Weight'):
    x = env['decimal.precision'].search([('name', '=', nombre)], limit=1)
    if x:
        print('   %-16s %s' % (nombre, x.digits))

print('\nredondeo que resulta (global, derivado de Product Unit):')
for nombre in ('L', 'ml', 'g', 'mg'):
    u = env['uom.uom'].search([('name', '=', nombre)], limit=1)
    if u:
        print('   %-6s %s' % (u.name, u.rounding))

env.cr.commit()
