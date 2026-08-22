# Verificar en staging cómo quedaron los consumibles después de nuestros scripts
consumibles = env['product.template'].search([
    ('default_code', 'like', 'CO%'),
    ('type', '!=', 'service'),
], order='default_code')

sin_cuarentena = consumibles.filtered(lambda p: not p.amunet_requires_quarantine)
con_cuarentena = consumibles.filtered(lambda p: p.amunet_requires_quarantine)
sin_secuencia = consumibles.filtered(lambda p: not p.product_variant_ids[:1].lot_sequence_id and p.tracking != 'none')

print(f"Total consumibles CO*: {len(consumibles)}")
print(f"  Sin cuarentena (req_q=False): {len(sin_cuarentena)}")
print(f"  Con cuarentena (req_q=True):  {len(con_cuarentena)}")
print(f"  Sin secuencia Amunet (tracking != none): {len(sin_secuencia)}")

if con_cuarentena:
    print("\nConsumibles que AÚN tienen cuarentena:")
    for p in con_cuarentena:
        print(f"  [{p.default_code}] {p.name}")

if sin_secuencia:
    print("\nConsumibles con tracking pero sin secuencia:")
    for p in sin_secuencia:
        prod = p.product_variant_ids[:1]
        print(f"  [{p.default_code}] {p.name} | tracking={p.tracking} | seq={prod.lot_sequence_id.code if prod.lot_sequence_id else 'NINGUNA'}")
