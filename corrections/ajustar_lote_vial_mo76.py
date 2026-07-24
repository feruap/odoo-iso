# MO 76 (0726/01/CAB, COVID DIAM-023, en progreso): el vial STBPR01 estaba reservado
# con el lote BPR01072601, pero el que fisicamente se surtio es BPR01042603 (CAD 2028-02).
# Se corrige el lote reservado en la operacion detallada (ajusta la reserva) y se pone la
# caducidad al lote correcto. Autorizado por Fernando 2026-07-24.
from odoo import fields as _f
Lot = env['stock.lot'].sudo()
lot_ok = Lot.search([('name', '=', 'BPR01042603'), ('product_id.default_code', '=', 'STBPR01')], limit=1)
assert lot_ok, 'no existe BPR01042603 de STBPR01'

# 1) Caducidad del lote correcto (CAD 2028-02 -> ultimo dia del mes)
if not lot_ok.expiration_date:
    lot_ok.expiration_date = _f.Datetime.to_datetime('2028-02-29 00:00:00')
    print('Caducidad BPR01042603 ->', lot_ok.expiration_date)
else:
    print('BPR01042603 ya tenia caducidad:', lot_ok.expiration_date)

# 2) Cambiar el lote reservado en el move_line del vial de la MO 76
ml = env['stock.move.line'].sudo().search([
    ('move_id.raw_material_production_id', '=', 76),
    ('product_id.default_code', '=', 'STBPR01')], limit=1)
assert ml, 'no se encontro el move_line del vial en MO 76'
print('Lote antes:', ml.lot_id.name, '| qty:', ml.quantity)
ml.write({'lot_id': lot_ok.id})
env.cr.commit()

# 3) Verificacion: move_line y reservas de quant
ml2 = env['stock.move.line'].sudo().browse(ml.id)
print('Lote despues:', ml2.lot_id.name)
env.cr.execute("""
  SELECT l.name, sl.complete_name, sq.quantity, sq.reserved_quantity
  FROM stock_quant sq JOIN stock_lot l ON l.id=sq.lot_id JOIN stock_location sl ON sl.id=sq.location_id
  WHERE l.name IN ('BPR01042603','BPR01072601') AND sq.quantity<>0 AND sl.usage='internal' ORDER BY l.name
""")
print('Reservas ahora:')
for row in env.cr.fetchall():
    print('   ', row)
print('LISTO')
