"""
Crea 3 análisis de prueba en staging listos para puntos de control y reporte:
  - STGOT02 (Gotero de 5 µL)
  - STREX01 (Vial reactivo de extracción)
  - MICAJ01 (Caja caple general)
"""

Check = env['amunet.quality.check']
Prod  = env['product.template']
Lot   = env['stock.lot']

productos = [
    ('STGOT02', 'GOT02-PRUEBA01'),
    ('STREX01', 'SREX01-PRUEBA01'),
    ('MICAJ01', 'MCAJ01-PRUEBA01'),
]

ids_creados = []

for codigo, lote_nombre in productos:
    tmpl = Prod.search([('default_code', '=', codigo)], limit=1)
    if not tmpl:
        print(f"  [{codigo}] producto no encontrado")
        continue

    pp = tmpl.product_variant_ids[:1]
    if not pp:
        print(f"  [{codigo}] sin variante")
        continue

    # Crear lote de prueba si no existe
    lot = Lot.search([('name', '=', lote_nombre), ('product_id', '=', pp.id)], limit=1)
    if not lot:
        lot = Lot.create({'name': lote_nombre, 'product_id': pp.id})

    check = Check.create({
        'product_id':    pp.id,
        'lot_id':        lot.id,
        'analysis_type': 'initial',
        'state':         'in_progress',
        'qty_sampling':  5,
    })

    # Cargar parámetros del producto (genera las líneas de puntos de control)
    check._load_product_parameters()
    check._auto_enable_anexo()

    ids_creados.append(check.id)
    print(f"  [{codigo}] id={check.id}  lote={lote_nombre}  "
          f"anexo='{check.anexo_titulo}'  col2='{check.anexo_col2_header}'")

env.cr.commit()

# Confirmar muestreo vía SQL (bypass validación de stock en staging)
if ids_creados:
    ids_str = ','.join(str(i) for i in ids_creados)
    env.cr.execute(f"""
        UPDATE amunet_quality_check
        SET sampling_confirmed = true
        WHERE id IN ({ids_str})
    """)
    env.cr.commit()
    print(f"\n  Muestreo confirmado en {len(ids_creados)} análisis (SQL bypass staging).")

print(f"\n✓ Análisis listos: {ids_creados}")
print("  Busca en Calidad → Análisis los IDs de arriba.")
