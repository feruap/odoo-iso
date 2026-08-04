"""
Crea 6 productos nuevos de materia prima usando huecos disponibles en la secuencia MPREC.
Aprobado por Karla Fernanda Palma Ramos (almacen.mp) el 2026-07-24.
"""
categ = env['product.category'].browse(18)  # Materia prima / Reactivo
uom_g  = env['uom.uom'].browse(14)
uom_ml = env.ref('uom.product_uom_milliliter')

productos = [
    # batch 2
    ('MPREC56', 'Cloruro de calcio',           uom_g),
    ('MPREC65', 'Sulfato de magnesio',          uom_g),
    ('MPREC66', 'Acetato de plomo',             uom_g),
    # batch 3
    ('MPREC67', 'Peptona de caseína',           uom_g),
    ('MPREC70', 'Ácido sulfúrico',              uom_ml),
    ('MPREC73', 'Ortosilicato de tetraetilo',   uom_ml),
]

print("Creando productos:\n")
for codigo, nombre, uom in productos:
    existe = env['product.template'].with_context(active_test=False).search([
        ('default_code','=',codigo)], limit=1)
    if existe:
        print(f"  ⚠️  {codigo} ya existe: {existe.name}")
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
        'amunet_requires_quarantine': False,
    })

    prefix_base = codigo[2:]
    seq_code   = f'amunet.lot.{prefix_base}.{tmpl.id}'
    seq_prefix = f'{prefix_base}%(month)s%(y)s'
    seq = env['ir.sequence'].sudo().search([('code','=',seq_code)], limit=1)
    if not seq:
        seq = env['ir.sequence'].sudo().create({
            'name': f'Lote Amunet — {nombre}',
            'code': seq_code,
            'prefix': seq_prefix,
            'padding': 2,
            'implementation': 'no_gap',
        })
    tmpl.product_variant_ids[:1].sudo().write({'lot_sequence_id': seq.id})
    print(f"  ✅ {codigo} — {nombre} | UoM: {uom.name} | Seq: {seq_prefix}01")

env.cr.commit()
print("\n✓ Listo")
