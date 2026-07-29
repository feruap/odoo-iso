"""
Crea CAR77, CAR78 y CAR79 (cartuchos correspondientes a SPHMC77/78/79).
Configuración basada en MPCAR17 (referencia): categ=Materia prima/Cartucho,
tracking=lot, use_expiration_date=True, uom=Units.

Autorizado por: Karla Fernanda Palma Ramos (almacen.mp@amunet.com.mx)
Fecha: 2026-07-29
"""

# Categoría y UoM de referencia (igual que MPCAR17)
ref = env['product.template'].with_context(active_test=False).search([
    ('default_code', '=', 'MPCAR17')], limit=1)
categ  = ref.categ_id
uom    = ref.uom_id
print(f"Referencia MPCAR17 → categ='{categ.complete_name}' | uom='{uom.name}'\n")

productos = [
    ('CAR77', 'Cartucho Transglutaminasa IgA (Anti-tTG)'),
    ('CAR78', 'Cartucho HPV E7'),
    ('CAR79', 'Cartucho CARBA 5 en 1'),
]

for codigo, nombre in productos:
    existe = env['product.template'].with_context(active_test=False).search([
        ('default_code', '=', codigo)], limit=1)
    if existe:
        print(f"⚠️  {codigo} ya existe: {existe.name}")
        continue

    tmpl = env['product.template'].with_context(amunet_alta_autorizada=True).sudo().create({
        'name': nombre,
        'default_code': codigo,
        'categ_id': categ.id,
        'type': 'consu',
        'is_storable': True,
        'tracking': 'lot',
        'uom_id': uom.id,
        'purchase_ok': True,
        'sale_ok': False,
        'use_expiration_date': True,
    })

    # Secuencia: CAR77%(month)s%(y)s
    prefix_base = codigo                           # CAR77, CAR78, CAR79
    seq_code    = f'amunet.lot.{prefix_base}.{tmpl.id}'
    seq_prefix  = f'{prefix_base}%(month)s%(y)s'

    seq = env['ir.sequence'].sudo().search([('code', '=', seq_code)], limit=1)
    if not seq:
        seq = env['ir.sequence'].sudo().create({
            'name': f'Lote Amunet — {nombre}',
            'code': seq_code,
            'prefix': seq_prefix,
            'padding': 2,
            'implementation': 'no_gap',
        })
    tmpl.product_variant_ids[:1].sudo().write({'lot_sequence_id': seq.id})

    print(f"✅ {codigo} — {nombre}")
    print(f"     categ={categ.complete_name} | uom={uom.name} | seq={seq_prefix}01")

env.cr.commit()
print("\n✓ Listo")
