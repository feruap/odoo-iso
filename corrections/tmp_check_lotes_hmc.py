"""Revisa todos los lotes existentes de SPHMC18, SPHMC56 y SPHMC62."""
for cod in ['SPHMC18', 'SPHMC56', 'SPHMC62']:
    tmpl = env['product.template'].with_context(active_test=False).search([
        ('default_code', '=', cod)], limit=1)
    prod = tmpl.product_variant_ids[:1]
    lotes = env['stock.lot'].search([('product_id', '=', prod.id)], order='name asc')
    print(f"[{cod}] {tmpl.name} — {len(lotes)} lote(s):")
    for l in lotes:
        q = env['stock.quant'].search([('lot_id','=',l.id),('location_id.usage','=','internal')], limit=1)
        print(f"  {l.name} | qty={q.quantity if q else 0}")
    print()
