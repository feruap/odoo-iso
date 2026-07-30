"""
Ajusta MPCAR07 lote CAR07032601 en AMPB/Existencias: 9,000 → 7,000 (-2,000).
Conteo físico confirmado por Karla Fernanda Palma Ramos (almacen.mp@amunet.com.mx).
Las 329 pzas en AMP/Existencias son correctas, no se tocan.

Fecha: 2026-07-30
"""
import os
if os.environ.get('RUN_CORRECTION_FORCE_PROD') != 'yes-i-know-what-i-do':
    print("PROTECCIÓN: define RUN_CORRECTION_FORCE_PROD=yes-i-know-what-i-do para ejecutar en prod")
    import sys; sys.exit(0)

loc_ampb = env['stock.location'].browse(20)   # AMPB/Existencias

tmpl = env['product.template'].with_context(active_test=False).search(
    [('default_code','=','MPCAR07')], limit=1)
prod = tmpl.product_variant_ids[:1]
lote = env['stock.lot'].search(
    [('name','=','CAR07032601'),('product_id','=',prod.id)], limit=1)

env['stock.quant']._update_available_quantity(prod, loc_ampb, -2000.0, lot_id=lote)

env.cr.commit()
print(f"✅ MPCAR07 / CAR07032601 — AMPB/Existencias: 9,000 → 7,000 (-2,000 pzas)")
