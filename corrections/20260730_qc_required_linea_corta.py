# -*- coding: utf-8 -*-
# Marca qc_required=True en TODOS los productos terminados de linea corta
# (pruebas rapidas inmunologicas + PCR rapida + reactivos terminados).
# Fernando 2026-07-30: toda linea corta debe requerir analisis C.C.
CATS = [
    'Producto terminado / Pruebas rápidas inmunológicas',
    'Producto terminado / Pruebas PCR rápida',
    'Producto terminado / Reactivo',
]
cats = env['product.category'].search([('complete_name', 'in', CATS)])
prods = env['product.template'].search([
    ('categ_id', 'in', cats.ids),
    ('active', '=', True),
])
por_marcar = prods.filtered(lambda p: p.qc_required is not True)
print("Categorias:", cats.mapped('complete_name'))
print("Total productos en categorias:", len(prods))
print("Ya con qc_required=True:", len(prods) - len(por_marcar))
print("A marcar:", len(por_marcar))
por_marcar.write({'qc_required': True})
print("MARCADOS:", ', '.join(sorted(por_marcar.mapped('default_code'))))
# Verificacion
restantes = env['product.template'].search_count([
    ('categ_id', 'in', cats.ids), ('active', '=', True),
    ('qc_required', '!=', True),
])
print("Verificacion - productos de esas categorias SIN qc_required tras el cambio:", restantes)
env.cr.commit()
