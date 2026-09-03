"""
Corrección: qty_to_return en QC/2026/00062 (MPCAR05, lote CAR05082601).
Cambio: 2 → 47 piezas. Autorizado por Diana Flores, 2026-09-02.
"""
QCheck = env['amunet.quality.check']
c = QCheck.browse(806)
if not c.exists():
    raise ValueError("QC id=806 no encontrado")

antes = c.qty_to_return
c.write({'qty_to_return': 47.0})
env.cr.commit()
despues = c.qty_to_return
print(f"✓ {c.name} | {c.product_id.default_code} | lote={c.lot_id.name}")
print(f"  qty_to_return: {antes} → {despues}")
