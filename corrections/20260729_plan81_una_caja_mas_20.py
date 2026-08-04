# Plan de empaque PE/0726/00007 (MO 81, Calprotectina 93 pzas): agregar una caja
# mas de la presentacion de 20 pzas (3 -> 4). Autorizado por Fernando 2026-07-29.
plan=env['amunet.packaging.plan'].sudo().search([('production_id','=',81)],order='id desc',limit=1)
ln=plan.line_ids.filtered(lambda l: l.package_qty==20)
print('antes: cajas de 20 =', ln.approved_box_qty)
ln.approved_box_qty = ln.approved_box_qty + 1
env.cr.commit()
print('despues: cajas de 20 =', ln.approved_box_qty)
total=sum(l.approved_box_qty*l.package_qty for l in plan.line_ids)
print('mezcla:', [(l.package_qty, l.approved_box_qty) for l in plan.line_ids.sorted('package_qty')], '| piezas planeadas:', total)
print('LISTO')
