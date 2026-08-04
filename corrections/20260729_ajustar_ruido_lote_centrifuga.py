# Limpia el ruido de inventario del lote CBV01032602 (centrifuga EQCBV01) del arranque.
# La existencia real (interna) es 1 en AMP/Existencias y NO se toca. Solo se corrigen
# las ubicaciones VIRTUALES para dejarlo igual que los 16 lotes hermanos:
#   Ajuste de inventario: +19 -> -1   |   Traslado entre almacenes: -10 -> 0
# Asi el lote neto = 0 (patron normal). Autorizado por Fernando 2026-07-29.
env.cr.execute("""
  SELECT loc.complete_name, loc.usage, sq.quantity
  FROM stock_quant sq JOIN stock_lot sl ON sl.id=sq.lot_id JOIN stock_location loc ON loc.id=sq.location_id
  WHERE sl.name='CBV01032602' ORDER BY loc.usage
""")
print('ANTES:', env.cr.fetchall())
env.cr.execute("""
  UPDATE stock_quant sq SET quantity=-1.0
  FROM stock_lot sl, stock_location loc
  WHERE sq.lot_id=sl.id AND sq.location_id=loc.id AND sl.name='CBV01032602' AND loc.usage='inventory'
""")
env.cr.execute("""
  UPDATE stock_quant sq SET quantity=0.0
  FROM stock_lot sl, stock_location loc
  WHERE sq.lot_id=sl.id AND sq.location_id=loc.id AND sl.name='CBV01032602' AND loc.usage='transit'
""")
env.cr.commit()
env.cr.execute("""
  SELECT loc.complete_name, loc.usage, sq.quantity
  FROM stock_quant sq JOIN stock_lot sl ON sl.id=sq.lot_id JOIN stock_location loc ON loc.id=sq.location_id
  WHERE sl.name='CBV01032602' ORDER BY loc.usage
""")
print('DESPUES:', env.cr.fetchall())
env.cr.execute("""
  SELECT COALESCE(SUM(sq.quantity),0) FROM stock_quant sq JOIN stock_lot sl ON sl.id=sq.lot_id
  JOIN stock_location loc ON loc.id=sq.location_id WHERE sl.name='CBV01032602' AND loc.usage='internal'
""")
print('ON-HAND interno (debe seguir 1):', env.cr.fetchone()[0])
print('LISTO')
