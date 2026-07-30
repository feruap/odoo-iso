"""
Crea subcategoría Consumible / Papelería y 39 productos con stock inicial.
Sin tracking de lote (son artículos de oficina).

Autorizado por: Karla Fernanda Palma Ramos (almacen.mp@amunet.com.mx)
Fecha: 2026-07-30
"""
loc = env['stock.location'].search([('complete_name','ilike','AMP/Existencias')], limit=1)
uom = env.ref('uom.product_uom_unit')
print(f"Ubicación: {loc.complete_name} | UoM: {uom.name}\n")

# ── 1. Crear subcategoría Papelería ─────────────────────────────────────────
categ_padre = env['product.category'].browse(4)  # Consumible
categ = env['product.category'].search([
    ('name','=','Papelería'), ('parent_id','=',categ_padre.id)], limit=1)
if not categ:
    categ = env['product.category'].create({
        'name': 'Papelería',
        'parent_id': categ_padre.id,
    })
    print(f"✅ Categoría creada: {categ.complete_name}")
else:
    print(f"ℹ️  Categoría ya existe: {categ.complete_name}")

# ── 2. Productos ─────────────────────────────────────────────────────────────
productos = [
    ('COPAP01', 'Lapicero rojo',                     6),
    ('COPAP02', 'Lapicero azul fino',                5),
    ('COPAP03', 'Lapicero azul mediano',            14),
    ('COPAP04', 'Lapicero azul punto de aguja',      5),
    ('COPAP05', 'Lapicero azul ultrafino',          16),
    ('COPAP06', 'Portaminas 0.5 mm',                 5),
    ('COPAP07', 'Lápiz de grafito',                  5),
    ('COPAP08', 'Block de notas',                    3),
    ('COPAP09', 'Clip N°1',                          7),
    ('COPAP10', 'Clip N°2',                          2),
    ('COPAP11', 'USB 32 GB',                         2),
    ('COPAP12', 'Marcatextos verde',                 5),
    ('COPAP13', 'Marcatextos naranja',               6),
    ('COPAP14', 'Marcatextos azul',                  3),
    ('COPAP15', 'Marcatextos rosa',                  4),
    ('COPAP16', 'Marcatextos amarillo',              2),
    ('COPAP17', 'Marcatextos morado',                2),
    ('COPAP18', 'Cinta adhesiva 12 mm x 33 m',      7),
    ('COPAP19', 'Plumones para pizarrón',            5),
    ('COPAP20', 'Grapa Standard',                    3),
    ('COPAP21', 'Goma de migajón',                   2),
    ('COPAP22', 'Agarrapapel 19 mm',                 8),
    ('COPAP23', 'Agarrapapel 32 mm',                 8),
    ('COPAP24', 'Agarrapapel 41 mm',                15),
    ('COPAP25', 'Puntillas 0.7 mm',                  1),
    ('COPAP26', 'Puntillas 0.5 mm',                  1),
    ('COPAP27', 'Cinta color rojo',                  3),
    ('COPAP28', 'Cinta color azul',                  3),
    ('COPAP29', 'Cinta color verde',                 3),
    ('COPAP30', 'Cinta color gris',                  1),
    ('COPAP31', 'Cinta color amarillo',              1),
    ('COPAP32', 'Cinta color rosa',                  1),
    ('COPAP33', 'Dedal de hule',                    10),
    ('COPAP34', 'Repuesto para cutter grande',       2),
    ('COPAP35', 'Marcador punto fino y extrafino',   8),
    ('COPAP36', 'Marcador permanente',               8),
    ('COPAP37', 'Compás',                            1),
    ('COPAP38', 'Sacapuntas',                        1),
    ('COPAP39', 'Lapicero 4 tintas',                 1),
]

print(f"\nCreando {len(productos)} productos:\n")
for codigo, nombre, qty in productos:
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
        'tracking': 'none',
        'uom_id': uom.id,
        'purchase_ok': True,
        'sale_ok': False,
    })
    prod = tmpl.product_variant_ids[:1]

    if qty > 0:
        env['stock.quant']._update_available_quantity(prod, loc, qty)

    print(f"  ✅ {codigo} — {nombre:<40s} qty={qty}")

env.cr.commit()
print(f"\n✓ Listo — {len(productos)} productos de papelería creados en {categ.complete_name}")
