# -*- coding: utf-8 -*-
"""Borrar MPAG02 (duplicada de MPAG18) y dar su codigo al anticuerpo de hCG.

Mery, 28-sep-2026:
  - MPAG02 "Antigeno de captura 25-OH-D" es ficha duplicada de MPAG18
    "Antigeno Vitamina D-BSA" (FPZ0188-3), que es la que de verdad se surte.
    Sin movimientos, sin lotes, sin receta y sin compras: se puede borrar de
    verdad, no hay trazabilidad que preservar.
  - MPANT09 (captura anti-hCG) lleva la clave de proveedor FPZ0612. Se le
    habia despegado BRCHBAS101 el 18-sep por ser de otro producto.
"""
mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

# --- 1. MPAG02: se comprueba que esta limpia ANTES de borrar ---------------
dup = env['product.product'].search([('default_code', '=', 'MPAG02')])
assert len(dup) == 1, 'Se esperaba una sola MPAG02, hay %d' % len(dup)
ataduras = {
    'movimientos': env['stock.move'].search_count([('product_id', '=', dup.id)]),
    'lotes': env['stock.lot'].search_count([('product_id', '=', dup.id)]),
    'existencias': env['stock.quant'].search_count([('product_id', '=', dup.id)]),
    'recetas': env['mrp.bom.line'].search_count([('product_id', '=', dup.id)]),
    'compras': env['purchase.order.line'].search_count([('product_id', '=', dup.id)]),
}
print('MPAG02 ataduras: %s' % ataduras)
assert not any(ataduras.values()), 'MPAG02 tiene historial: NO se borra, se archiva'

tmpl = dup.product_tmpl_id
tmpl.unlink()
print('MPAG02 borrada')

# --- 2. Codigo de proveedor del anticuerpo de captura de hCG ---------------
ant = env['product.product'].search([('default_code', '=', 'MPANT09')], limit=1)
assert ant, 'No existe MPANT09'
ya = env['product.supplierinfo'].search([('product_code', '=', 'FPZ0612')])
assert not ya, 'FPZ0612 ya esta en %s' % ya.mapped('product_tmpl_id.default_code')

si = env['product.supplierinfo'].search([
    '|', ('product_tmpl_id', '=', ant.product_tmpl_id.id), ('product_id', '=', ant.id)])
assert len(si) == 1, 'Se esperaba un solo proveedor en MPANT09, hay %d' % len(si)
si.write({'product_code': 'FPZ0612'})
print('MPANT09 -> %s (%s)' % (si.product_code, si.partner_id.name))

env.cr.commit()

print('--- verificacion ---')
print('MPAG02 existe: %s' % bool(env['product.product'].search_count([('default_code', '=', 'MPAG02')])))
print('MPAG18: %s' % env['product.product'].search([('default_code', '=', 'MPAG18')]).seller_ids.mapped('product_code'))
print('MPANT09: %s' % env['product.product'].search([('default_code', '=', 'MPANT09')]).seller_ids.mapped('product_code'))
