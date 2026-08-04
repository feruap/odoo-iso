"""Tabla completa: nombre, clave, lote, ubicación y cantidad."""
lotes_check = [
    ('MPCAC01', 'CAC01032601'),
    ('MPCAR07', 'CAR07032601'),
    ('MPCAR21', 'CAR21032601'),
    ('MPCAR24', 'CAR24032601'),
    ('STGOT01', 'GOT01032601'),
    ('EQCBV01', 'CBV01032602'),
    ('MPANT04', 'ANT04062601'),
    ('MPANT05', 'ANT05062601'),
    ('MPANT05', 'ANT05062602'),
    ('MPANT07', 'ANT07062601'),
    ('MPANT08', 'ANT08062601'),
    ('MPANT10', 'ANT10062601'),
    ('MPANT12', 'ANT12062601'),
    ('MPANT13', 'ANT13062601'),
    ('MPCAR05', 'CAR05032601'),
    ('SPHMC66', 'HMC66032601'),
]

print(f"{'Nombre':<45} {'Clave':<10} {'Lote':<18} {'Ubicación':<30} {'Qty':>8}")
print("-" * 120)

for cod, lot_name in lotes_check:
    tmpl = env['product.template'].with_context(active_test=False).search([
        ('default_code','=',cod)], limit=1)
    prod = tmpl.product_variant_ids[:1]
    lote = env['stock.lot'].search([
        ('name','=',lot_name),('product_id','=',prod.id)], limit=1)
    if not lote:
        print(f"{'(lote no encontrado)':<45} {cod:<10} {lot_name:<18} {'—':<30} {'—':>8}")
        continue
    quants = env['stock.quant'].search([
        ('lot_id','=',lote.id), ('location_id.usage','=','internal'),
        ('quantity','>',0)])
    if not quants:
        print(f"{tmpl.name:<45} {cod:<10} {lot_name:<18} {'(sin existencia)':<30} {'0':>8}")
    for q in quants:
        print(f"{tmpl.name:<45} {cod:<10} {lot_name:<18} {q.location_id.complete_name:<30} {q.quantity:>8.0f}")
