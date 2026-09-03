"""
Corrección: qty_to_return en QC/2026/00067 (MPCAR33, lote CAR33082601).
Cambio: 9 → 31 piezas. Autorizado por Diana Flores, 2026-09-02.
"""
QCheck = env['amunet.quality.check']
c = QCheck.search([('name', '=', 'QC/2026/00067')], limit=1)
if not c:
    raise ValueError("QC/2026/00067 no encontrado")

antes = c.qty_to_return
c.write({'qty_to_return': 31.0})
env.cr.commit()
despues = c.qty_to_return
print(f"✓ {c.name} | {c.product_id.default_code} | lote={c.lot_id.name}")
print(f"  qty_to_return: {antes} → {despues}")
