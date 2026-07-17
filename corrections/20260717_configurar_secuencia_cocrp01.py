"""
Configura COCRP01 (Contenedor RPBI para líquidos) en staging:
  1. Cambia tracking a 'lot' (igual que producción)
  2. Crea secuencia Amunet propia con prefijo CRP01%(month)s%(y)s
     → genera lotes: CRP01072601, CRP01072602, ... (reset mensual)
  3. Asigna la secuencia al producto
"""
env = env(su=True)

# 1. Obtener el producto
tmpl = env['product.template'].search([('default_code', '=', 'COCRP01')], limit=1)
if not tmpl:
    raise Exception("COCRP01 no encontrado")

print(f"Producto: {tmpl.name} | tracking actual: {tmpl.tracking}")

# 2. Cambiar tracking a 'lot'
tmpl.write({'tracking': 'lot'})
print(f"tracking → lot")

# 3. Crear (o reusar) secuencia Amunet propia
seq_code = f"amunet.lot.CRP01.{tmpl.id}"
existing_seq = env['ir.sequence'].search([('code', '=', seq_code)], limit=1)

if existing_seq:
    print(f"Secuencia existente: {existing_seq.name} | prefix: {existing_seq.prefix}")
    seq = existing_seq
else:
    seq = env['ir.sequence'].sudo().create({
        'name': f'Lote CRP01 - {tmpl.name}',
        'code': seq_code,
        'implementation': 'standard',
        'prefix': 'CRP01%(month)s%(y)s',
        'padding': 2,
        'number_next': 1,
        'number_increment': 1,
        'use_date_range': False,
        'company_id': 1,
    })
    print(f"Secuencia creada: {seq.name} | prefix: {seq.prefix} | code: {seq.code}")

# 4. Asignar secuencia y activar reset mensual
tmpl.write({
    'lot_sequence_id': seq.id,
    'amunet_lot_reset_monthly': True,
})
print(f"lot_sequence_id → {seq.id} ({seq.code})")
print(f"amunet_lot_reset_monthly → True")

# 5. Verificar que _is_amunet_auto_lot_enabled retorna True
producto = tmpl.product_variant_ids[0]
enabled = tmpl._is_amunet_auto_lot_enabled()
print(f"_is_amunet_auto_lot_enabled: {enabled}")

# 6. Preview del próximo lote que generaría
try:
    proximos = producto._amunet_next_lot_names(3)
    print(f"Próximos lotes (preview): {proximos}")
except Exception as e:
    print(f"Error al previsualizar lotes: {e}")

env.cr.commit()
print("✓ Configuración guardada")
