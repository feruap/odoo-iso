# -*- coding: utf-8 -*-
# Cambio de bolsa metalizada COBME01 -> COBME02 en los medios de cultivo.
# Autorizado por Fernando 2026-07-10.
#  1) Presentaciones: comp 99 (Salmonella, pres 34) y comp 100 (Listeria, pres 35).
#  2) Orden en curso 0726/02/R01 (MO 58): move 5378 COBME01 (2 pz) -> COBME02.
# COBME02 = variante 1840 (lote, 92 pz existencia). COBME01 = 1820.

COBME02_ID = 1840

# --- 1) Presentaciones ---
comps = env['amunet.packaging.presentation.component'].browse([99, 100]).exists()
for comp in comps:
    antes = comp.product_id.default_code
    comp.write({'product_id': COBME02_ID})
    print("  [PRESENTACION %s] %s -> %s (qty_per_box=%s)" % (
        comp.presentation_id.name, antes, comp.product_id.default_code, comp.qty_per_box))

# --- 2) Orden 0726/02/R01 ---
move = env['stock.move'].browse(5378).exists()
if not move:
    print("  [ORDEN] move 5378 no existe, salto")
elif move.state == 'done':
    print("  [ORDEN] move 5378 ya esta HECHO, no se toca")
else:
    cob2 = env['product.product'].browse(COBME02_ID)
    antes = move.product_id.default_code
    move._do_unreserve()
    move.write({'product_id': cob2.id, 'product_uom': cob2.uom_id.id})
    move._action_assign()
    print("  [ORDEN %s] move 5378 %s -> %s | demanda=%s reservado=%s estado=%s" % (
        move.raw_material_production_id.name, antes, move.product_id.default_code,
        move.product_uom_qty, move.quantity, move.state))

env.cr.commit()
print("LISTO")
