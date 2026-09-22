# -*- coding: utf-8 -*-
"""Redondeo de unidades a 4 decimales.

Todas las unidades estaban en 0.01. Con eso Odoo no podia expresar una
cantidad como 333 ml de un producto que se lleva en LITROS: 0.333 L se
redondeaba a 0.33 (330 ml), y los 3 ml sobrantes se iban a un segundo lote.
De ahi salia el lote partido que chocaba con el candado ISO de un lote por
componente. Decision de Mery, 22-sep-2026: cuatro decimales.

Cambia:
  - uom.uom.rounding  -> 0.0001 en todas las unidades que estuvieran por arriba
  - decimal.precision 'Product Unit' y 'Stock Weight' -> 4 digitos

NO toca 'Product Price': los precios no entran en este cambio.

Correr con:
  /opt/odoo/scripts/run_correction.sh production precision_4_decimales_2026-09-22.py
"""

cambiadas = 0
for u in env['uom.uom'].search([]):
    if u.rounding and u.rounding > 0.0001:
        print('  %-28s %s -> 0.0001' % (u.name, u.rounding))
        u.sudo().rounding = 0.0001
        cambiadas += 1
print('\nunidades ajustadas: %d' % cambiadas)

for nombre in ('Product Unit', 'Stock Weight'):
    d = env['decimal.precision'].search([('name', '=', nombre)], limit=1)
    if d and d.digits < 4:
        print('  precision %-16s %s -> 4' % (nombre, d.digits))
        d.sudo().digits = 4

precio = env['decimal.precision'].search([('name', '=', 'Product Price')], limit=1)
print('\nProduct Price se deja en %s (no entra en este cambio)' % (precio.digits if precio else '-'))

env.cr.commit()
