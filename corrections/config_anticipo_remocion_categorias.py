# -*- coding: utf-8 -*-
# Configura el anticipo de la fecha de remocion por categoria (politica Amunet,
# decidido por Fernando 2026-07-14): Materia prima=1 mes, Soluciones=7 dias,
# Terminados/Pruebas rapidas=4 meses. Las subcategorias heredan del padre; el
# resto usa 1 mes por defecto. Requiere amunet_lot v19.0.1.0.7 (campo nuevo).
Cat = env['product.category']

def setcat(complete_name, val, unit):
    c = Cat.search([('complete_name', '=', complete_name)], limit=1)
    if c:
        c.write({'amunet_removal_value': val, 'amunet_removal_unit': unit})
        print("  set %-52s -> %s %s" % (complete_name, val, unit))
    else:
        print("  NO encontrada:", complete_name)

setcat('Materia prima', 1, 'months')
setcat('Semiprocesado / Soluciones de trabajo', 7, 'days')
setcat('Producto terminado / Pruebas rápidas inmunológicas', 4, 'months')
env.cr.commit()
print("LISTO")
