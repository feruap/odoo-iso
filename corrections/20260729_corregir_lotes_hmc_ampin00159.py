"""
Corrige los números de lote mal generados en AMP/IN/00159.
El script anterior usó seq.next_by_id() en lugar del método gap-free de Amunet.

Correcciones:
  HMC18072604 → HMC18072602 (Dengue)
  HMC56072603 → HMC56072602 (Chikungunya)
  HMC62072603 → HMC62072602 (Zika)

Autorizado por: Karla Fernanda Palma Ramos (almacen.mp@amunet.com.mx)
Fecha: 2026-07-29
"""
correcciones = [
    ('SPHMC18', 'HMC18072604', 'HMC18072602'),
    ('SPHMC56', 'HMC56072603', 'HMC56072602'),
    ('SPHMC62', 'HMC62072603', 'HMC62072602'),
]

for cod, nombre_malo, nombre_correcto in correcciones:
    tmpl = env['product.template'].with_context(active_test=False).search([
        ('default_code', '=', cod)], limit=1)
    prod = tmpl.product_variant_ids[:1]

    # Verificar que el nombre correcto no exista ya
    existe = env['stock.lot'].search([
        ('name', '=', nombre_correcto), ('product_id', '=', prod.id)], limit=1)
    if existe:
        print(f"⚠️  [{cod}] {nombre_correcto} ya existe, no se puede renombrar")
        continue

    lote = env['stock.lot'].search([
        ('name', '=', nombre_malo), ('product_id', '=', prod.id)], limit=1)
    if not lote:
        print(f"⚠️  [{cod}] {nombre_malo} no encontrado")
        continue

    lote.sudo().write({'name': nombre_correcto})
    print(f"✅ [{cod}] {nombre_malo} → {nombre_correcto}")

env.cr.commit()
print("\n✓ Listo")
