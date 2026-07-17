"""
Para todos los consumibles en staging:
  1. Quita el control de calidad (amunet_req_quality_control=False)
  2. Cambia tracking a 'lot' donde estaba en 'none'
  3. Crea secuencia Amunet propia para los que usan la genérica stock.lot.serial
     El prefijo sigue el patrón: default_code sin "CO" + %(month)s%(y)s
     Ej: COBME01 → BME01%(month)s%(y)s → lotes BME01072601, BME01072602...
"""
env = env(su=True)

# IDs de categoría Consumible y sus subcategorías
cat_result = env['product.category'].search([
    '|', ('id', '=', 4), ('parent_id', '=', 4)
])
cat_ids = cat_result.ids
print(f"Categorías consumibles: {cat_ids}")

# Obtener todos los consumibles activos
productos = env['product.template'].search([
    ('categ_id', 'in', cat_ids),
    ('active', '=', True),
])
print(f"Total consumibles encontrados: {len(productos)}")

sin_calidad = 0
tracking_corregido = 0
secuencias_creadas = 0
ya_tienen_secuencia = 0

for pt in productos:
    code = pt.default_code or ''
    cambios = {}

    # 1. Quitar control de calidad
    if pt.amunet_req_quality_control:
        cambios['amunet_req_quality_control'] = False
        sin_calidad += 1

    # 2. Corregir tracking='none' a 'lot'
    if pt.tracking == 'none':
        cambios['tracking'] = 'lot'
        tracking_corregido += 1

    # Aplicar cambios de campos simples primero
    if cambios:
        pt.write(cambios)

    # 3. Crear secuencia Amunet si usa la genérica o no tiene prefijo propio
    seq = pt.lot_sequence_id
    necesita_secuencia = (
        not seq or
        not seq.code or
        not seq.code.startswith('amunet.lot.')
    )

    if necesita_secuencia and code:
        # Prefijo: quitar "CO" del inicio del default_code
        prefix_base = code[2:] if code.upper().startswith('CO') else code
        seq_prefix = f"{prefix_base}%(month)s%(y)s"
        seq_code = f"amunet.lot.{prefix_base}.{pt.id}"

        # Buscar si ya existe
        existing = env['ir.sequence'].search([('code', '=', seq_code)], limit=1)
        if existing:
            pt.write({
                'lot_sequence_id': existing.id,
                'amunet_lot_reset_monthly': True,
            })
            ya_tienen_secuencia += 1
            print(f"  [reuso] {code} → {existing.prefix}")
        else:
            nueva_seq = env['ir.sequence'].sudo().create({
                'name': f'Lote {prefix_base} - {pt.name}',
                'code': seq_code,
                'implementation': 'standard',
                'prefix': seq_prefix,
                'padding': 2,
                'number_next': 1,
                'number_increment': 1,
                'use_date_range': False,
                'company_id': 1,
            })
            pt.write({
                'lot_sequence_id': nueva_seq.id,
                'amunet_lot_reset_monthly': True,
            })
            secuencias_creadas += 1
            print(f"  [nueva] {code} → {seq_prefix}")
    elif not necesita_secuencia:
        # Ya tiene su secuencia Amunet correcta
        pass

env.cr.commit()

print("\n=== RESUMEN ===")
print(f"  Calidad desactivada:     {sin_calidad} productos")
print(f"  Tracking corregido:      {tracking_corregido} productos (none → lot)")
print(f"  Secuencias nuevas:       {secuencias_creadas} productos")
print(f"  Secuencias reutilizadas: {ya_tienen_secuencia} productos")
print("✓ Listo")
