# -*- coding: utf-8 -*-
# Marca como almacenables (is_storable=True) 3 productos que quedaron como
# "consumible no almacenable" por error, cuando sus pares (69/70 anticuerpos,
# 26/28 soluciones) SI son almacenables. Sin el flag no aparece el boton
# "Actualizar cantidad" ni llevan inventario/lotes. Pedido de Fernando 2026-07-14.
#   1733 MPANT03 - Anticuerpo policlonal anti-raton (control)
#   2034 SPACL01 - Acido cloroaurico 1%
#   2033 SPCDS01 - Citrato de sodio 1%
Pt = env['product.template']
prods = Pt.browse([1733, 2034, 2033]).exists()
print("Antes:")
for p in prods:
    print("  %s %s -> is_storable=%s" % (p.id, p.default_code, p.is_storable))

prods.write({'is_storable': True})
env.cr.commit()

print("Despues:")
for p in Pt.browse([1733, 2034, 2033]):
    print("  %s %s -> is_storable=%s" % (p.id, p.default_code, p.is_storable))
print("LISTO")
