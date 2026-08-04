# Analisis de calidad del ARRANQUE (lote *032601) que quedaron pendientes.
# Autorizado por Fernando 2026-07-29.
#  - 2a (sin existencia real): archivar analisis.  MPCAR05/CAR05032601, SPHMC66/HMC66032601
#  - 2b (con stock real, del arranque): archivar analisis + limpiar ruido de inventario.
#    Se conserva el stock real (ubicaciones internas). Solo se corrigen las
#    ubicaciones VIRTUALES: Traslado entre almacenes -> 0 y Ajuste de inventario
#    se rebalancea para que el lote neto = 0 (patron sano). Los movimientos reales
#    (Produccion, Clientes) se conservan.

ARCHIVAR = [
    ('MPCAR05', 'CAR05032601'), ('SPHMC66', 'HMC66032601'),          # 2a
    ('MPCAC01', 'CAC01032601'), ('MPCAR07', 'CAR07032601'),          # 2b
    ('MPCAR21', 'CAR21032601'), ('MPCAR24', 'CAR24032601'),
    ('STGOT01', 'GOT01032601'),
]
n = 0
for code, lot in ARCHIVAR:
    qc = env['amunet.quality.check'].sudo().search([
        ('product_id.default_code', '=', code),
        ('lot_id.name', '=', lot),
        ('state', '!=', 'done'), ('active', '=', True),
    ])
    if qc:
        qc.write({'active': False,
                  'change_reason': 'Archivado 2026-07-29: analisis del arranque (lote 032601). '
                                   'Stock del arranque ya dado por bueno; sin analisis retroactivo. '
                                   'Autorizado por Fernando.'})
        n += len(qc)
        print('archivado', code, lot, qc.mapped('name'))
env.cr.commit()
print('Total analisis archivados:', n)

# Limpiar ruido de inventario SOLO en los 2b (con stock real)
LIMPIAR = ['CAC01032601', 'CAR07032601', 'CAR21032601', 'CAR24032601', 'GOT01032601']
for lot in LIMPIAR:
    # transito -> 0
    env.cr.execute("""UPDATE stock_quant sq SET quantity=0
        FROM stock_lot sl, stock_location loc
        WHERE sq.lot_id=sl.id AND sq.location_id=loc.id AND sl.name=%s AND loc.usage='transit'""", (lot,))
    # sumar todo lo demas (interno + produccion + clientes + ...) EXCEPTO ajuste de inventario
    env.cr.execute("""SELECT COALESCE(SUM(sq.quantity),0)
        FROM stock_quant sq JOIN stock_lot sl ON sl.id=sq.lot_id JOIN stock_location loc ON loc.id=sq.location_id
        WHERE sl.name=%s AND loc.usage<>'inventory'""", (lot,))
    otros = env.cr.fetchone()[0]
    # ajuste de inventario = -(todo lo demas)  -> total 0
    env.cr.execute("""UPDATE stock_quant sq SET quantity=%s
        FROM stock_lot sl, stock_location loc
        WHERE sq.lot_id=sl.id AND sq.location_id=loc.id AND sl.name=%s AND loc.usage='inventory'""",
        (-otros, lot))
env.cr.commit()

# Verificacion
print('--- verificacion 2b ---')
for lot in LIMPIAR:
    env.cr.execute("""SELECT ROUND(SUM(sq.quantity)::numeric,2),
        ROUND(SUM(CASE WHEN loc.usage='internal' THEN sq.quantity ELSE 0 END)::numeric,2)
        FROM stock_quant sq JOIN stock_lot sl ON sl.id=sq.lot_id JOIN stock_location loc ON loc.id=sq.location_id
        WHERE sl.name=%s""", (lot,))
    total, interno = env.cr.fetchone()
    print('  %s: neto=%s | existencia(interno)=%s' % (lot, total, interno))
print('LISTO')
