"""
Devuelve al inventario los materiales movidos por la orden de prueba SMP/26/00159.

T/AMP/ENC/00153 (done) movió:
  - COBCE01 BCE01072601: 1 pza  AMP/Existencias → Consumo - Solicitudes de Material
  - COBCE02 BCE02062601: 4 pzas AMP/Existencias → Consumo - Solicitudes de Material

La orden era de prueba y la persona pidió revertirla. El SMP y el picking
se dejan como historial (no se pueden cancelar en estado done); solo se
corrigen los quants.

Autorizado por: Karla Fernanda Palma Ramos (almacen.mp@amunet.com.mx)
Fecha: 2026-07-30
"""
import os
if os.environ.get('RUN_CORRECTION_FORCE_PROD') != 'yes-i-know-what-i-do':
    print("PROTECCIÓN: define RUN_CORRECTION_FORCE_PROD=yes-i-know-what-i-do para ejecutar en prod")
    import sys; sys.exit(0)

loc_existencias = env['stock.location'].browse(5)    # AMP/Existencias
loc_consumo     = env['stock.location'].browse(44)   # Consumo - Solicitudes de Material

ajustes = [
    # (clave, lote_nombre, qty_devolver)
    ('COBCE01', 'BCE01072601', 1.0),
    ('COBCE02', 'BCE02062601', 4.0),
]

for clave, lote_nombre, qty in ajustes:
    tmpl = env['product.template'].with_context(active_test=False).search(
        [('default_code', '=', clave)], limit=1)
    prod = tmpl.product_variant_ids[:1]
    lote = env['stock.lot'].search(
        [('name', '=', lote_nombre), ('product_id', '=', prod.id)], limit=1)
    if not prod or not lote:
        print(f"  ⚠️  No encontrado: {clave} / {lote_nombre}")
        continue

    # Quitar de Consumo - Solicitudes de Material
    env['stock.quant']._update_available_quantity(prod, loc_consumo, -qty, lot_id=lote)
    # Devolver a AMP/Existencias
    env['stock.quant']._update_available_quantity(prod, loc_existencias, qty, lot_id=lote)

    print(f"  ✅ {clave} lote {lote_nombre}: devuelto {qty} pza(s) a AMP/Existencias")

env.cr.commit()
print("\n✓ Listo — materiales de SMP/26/00159 devueltos a AMP/Existencias")
print("  El SMP y T/AMP/ENC/00153 quedan como historial (estado done, no se revierten).")
