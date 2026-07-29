"""
Activa tracking por lote, caducidad y secuencia Amunet para SPHMC77, 78 y 79.
Igualando la configuración de SPHMC18/56/62 (referencia).

Autorizado por: Karla Fernanda Palma Ramos (almacen.mp@amunet.com.mx)
Fecha: 2026-07-29
"""
codigos = ['SPHMC77', 'SPHMC78', 'SPHMC79']

for cod in codigos:
    tmpl = env['product.template'].with_context(active_test=False).search([
        ('default_code', '=', cod)], limit=1)
    if not tmpl:
        print(f"⚠️  {cod} no encontrado")
        continue

    prod = tmpl.product_variant_ids[:1]

    # 1. Activar tracking y caducidad
    tmpl.sudo().write({
        'tracking': 'lot',
        'use_expiration_date': True,
    })

    # 2. Crear secuencia Amunet: SPHMC77[2:] = HMC77
    prefix_base = cod[2:]                          # HMC77, HMC78, HMC79
    seq_code    = f'amunet.lot.{prefix_base}.{tmpl.id}'
    seq_prefix  = f'{prefix_base}%(month)s%(y)s'

    seq = env['ir.sequence'].sudo().search([('code', '=', seq_code)], limit=1)
    if not seq:
        seq = env['ir.sequence'].sudo().create({
            'name': f'Lote Amunet — {tmpl.name}',
            'code': seq_code,
            'prefix': seq_prefix,
            'padding': 2,
            'implementation': 'no_gap',
        })
    prod.sudo().write({'lot_sequence_id': seq.id})

    print(f"✅ [{cod}] {tmpl.name[:45]}")
    print(f"     tracking=lot | use_expiration_date=True | seq={seq_prefix}01")

env.cr.commit()
print("\n✓ Listo — SPHMC77, 78 y 79 configuradas igual que SPHMC18/56/62")
