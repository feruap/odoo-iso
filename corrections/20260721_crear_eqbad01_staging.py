"""
Crea EQBAD01 (Balanza digital) en staging, copiando la configuración de producción.
Datos origen (producción 2026-07-21):
  id=2142, type=consu, tracking=lot, categ=Producto terminado/Equipo,
  use_expiration_date=True, amunet_requires_quarantine=False
Además crea la secuencia Amunet BAD01%(month)s%(y)s.
"""

# Buscar categoría en staging por nombre completo
categ = env['product.category'].search([
    ('complete_name', '=', 'Producto terminado / Equipo')
], limit=1)
if not categ:
    # Intentar solo "Equipo"
    categ = env['product.category'].search([
        ('name', '=', 'Equipo')
    ], limit=1)
if not categ:
    raise ValueError("No se encontró la categoría 'Equipo' en staging. Revisar catálogo.")

uom = env.ref('uom.product_uom_unit')

# Verificar que no exista ya
existente = env['product.template'].with_context(active_test=False).search([
    ('default_code', '=', 'EQBAD01')
], limit=1)
if existente:
    print(f"Ya existe en staging: id={existente.id}, nombre={existente.name}")
else:
    tmpl = env['product.template'].sudo().with_context(amunet_alta_autorizada=True).create({
        'name': 'Balanza digital',
        'default_code': 'EQBAD01',
        'type': 'consu',
        'tracking': 'lot',
        'categ_id': categ.id,
        'uom_id': uom.id,
        'use_expiration_date': True,
        'amunet_requires_quarantine': False,
        'active': True,
    })
    print(f"Producto creado: id={tmpl.id}, nombre={tmpl.name}, código={tmpl.default_code}")

    # Crear secuencia Amunet
    prod = tmpl.product_variant_ids[:1]
    prefix_base = 'BAD01'
    seq_code = f'amunet.lot.{prefix_base}.{tmpl.id}'
    seq_prefix = f'{prefix_base}%(month)s%(y)s'

    seq = env['ir.sequence'].sudo().search([('code', '=', seq_code)], limit=1)
    if not seq:
        seq = env['ir.sequence'].sudo().create({
            'name': f'Lote Amunet — Balanza digital',
            'code': seq_code,
            'prefix': seq_prefix,
            'padding': 2,
            'implementation': 'no_gap',
        })
        print(f"Secuencia creada: {seq_prefix}XX")

    prod.sudo().write({'lot_sequence_id': seq.id})
    print(f"Secuencia asignada a la variante (id={prod.id})")
    print(f"\n✓ EQBAD01 listo en staging")
    print(f"  Categoría: {categ.complete_name} (id={categ.id})")
    print(f"  UoM: {uom.name} (id={uom.id})")
    print(f"  Secuencia: {seq_prefix}01, {seq_prefix}02, ...")

env.cr.commit()
