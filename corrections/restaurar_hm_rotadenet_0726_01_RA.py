# MO 0726/01/RA (id 74, DMRAV01 ROTADENET, 225 pzas, en progreso). Fernando borro
# por error la linea de hoja maestra: el move 5856 (SPHMC27) quedo con cantidad 0.
# Segun BoM la hoja maestra consume 0.40 por pieza -> 225 * 0.40 = 90. Se restaura
# la demanda y se re-reserva. Autorizado por Fernando 2026-07-22.
mo = env['mrp.production'].sudo().browse(74)
assert mo.exists() and mo.name == '0726/01/RA', 'MO incorrecta'
mv = env['stock.move'].sudo().browse(5856)
assert mv.exists() and mv.raw_material_production_id.id == 74, 'move incorrecto'
assert mv.product_id.default_code == 'SPHMC27', 'no es la hoja maestra'

esperado = mo.product_qty * 0.40
print('MO:', mo.name, '| qty:', mo.product_qty, '| HM antes:', mv.product_uom_qty, mv.state)
mv.write({'product_uom_qty': esperado})
mo.action_assign()
env.cr.commit()

mv = env['stock.move'].sudo().browse(5856)
print('HM despues:', mv.product_uom_qty, '| reservado:', mv.quantity, '| estado:', mv.state)
print('LISTO')
