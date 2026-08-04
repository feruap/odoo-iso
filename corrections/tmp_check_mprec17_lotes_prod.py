"""
Solo lectura: verifica lotes de MPREC17 en producción y si existe MPREC82.
"""
tmpl17 = env['product.template'].with_context(active_test=False).search([
    ('default_code', '=', 'MPREC17')], limit=1)
print(f"MPREC17: {tmpl17.name if tmpl17 else 'NO EXISTE'}")
if tmpl17:
    prod17 = tmpl17.product_variant_ids[:1]
    lotes = env['stock.lot'].search([('product_id', '=', prod17.id)])
    for l in lotes:
        quant = env['stock.quant'].search([('lot_id', '=', l.id), ('location_id.usage', '=', 'internal')], limit=1)
        print(f"  Lote: {l.name} | Prov: {l.factory_lot_id.name if l.factory_lot_id else '-'} | qty={quant.quantity if quant else 0}")

print()
tmpl82 = env['product.template'].with_context(active_test=False).search([
    ('default_code', '=', 'MPREC82')], limit=1)
print(f"MPREC82: {tmpl82.name if tmpl82 else 'NO EXISTE'}")
