# Ajuste BoM Calprotectina (DMCAL01): hoja maestra SPHMC55 de 0.40 -> 0.30 cm/pieza,
# y en consecuencia la MO 0726/01/CAL (id 81, 70 pzas, en progreso): demanda de
# SPHMC55 de 28 -> 21. Autorizado por Fernando 2026-07-29.
bom=env['mrp.bom'].sudo().search([('product_tmpl_id.default_code','=','DMCAL01')],limit=1)
line=bom.bom_line_ids.filtered(lambda l: l.product_id.default_code=='SPHMC55')
print('BoM antes:', line.product_qty)
line.product_qty=0.30
print('BoM despues:', line.product_qty)

mo=env['mrp.production'].sudo().browse(81)
move=mo.move_raw_ids.filtered(lambda m: m.product_id.default_code=='SPHMC55')
nueva=0.30*mo.product_qty
print('MO 81 SPHMC55 demanda antes:', move.product_uom_qty, '| state:', move.state, '| nueva:', nueva)
move._do_unreserve()
move.product_uom_qty=nueva
move._action_assign()
env.cr.commit()
print('MO 81 SPHMC55 demanda despues:', move.product_uom_qty, '| reservado:', move.quantity, '| state:', move.state)
print('LISTO')
