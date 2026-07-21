"""
Crea secuencias Amunet para reactivos (MPREC27-91), equipos sin secuencia y
consumibles varios que aún usan stock.lot.serial.
Patrón: prefijo = default_code[2:] + %(month)s%(y)s, padding=2.
"""
# Productos a configurar: (default_code, prefijo_base)
# Para MP* quitar "MP", para EQ* quitar "EQ", para CO* quitar "CO"
a_configurar = []

# Reactivos MPREC27-MPREC91
for p in env['product.template'].search([
    ('default_code', 'like', 'MPREC%'),
    ('tracking', '!=', 'none'),
], order='default_code'):
    prod = p.product_variant_ids[:1]
    if not prod.lot_sequence_id or not prod.lot_sequence_id.code.startswith('amunet.lot.'):
        a_configurar.append(p)

# Equipos sin secuencia (no refacciones)
for codigo in ['EQAMC01', 'EQEPV01', 'EQBSD01', 'EQRMA01', 'EQTRV01']:
    p = env['product.template'].search([('default_code', '=', codigo)], limit=1)
    if p:
        a_configurar.append(p)

# Consumibles varios sin secuencia
for codigo in ['COCAT01', 'COCEN01', 'COPIS01', 'COTPH01']:
    p = env['product.template'].search([('default_code', '=', codigo)], limit=1)
    if p:
        a_configurar.append(p)

print(f"Productos a configurar: {len(a_configurar)}")
creadas = 0
ya_tenia = 0

for tmpl in a_configurar:
    prod = tmpl.product_variant_ids[:1]
    if not prod:
        print(f"  [{tmpl.default_code}] Sin variante, omitido")
        continue

    # Ya tiene secuencia Amunet?
    if prod.lot_sequence_id and prod.lot_sequence_id.code.startswith('amunet.lot.'):
        ya_tenia += 1
        continue

    code = tmpl.default_code or ''
    prefix_base = code[2:]  # Quitar primeros 2 chars (MP, EQ, CO)
    seq_code = f'amunet.lot.{prefix_base}.{tmpl.id}'
    seq_prefix = f'{prefix_base}%(month)s%(y)s'

    # Verificar si ya existe la secuencia
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
    print(f"  [{code}] {tmpl.name[:50]} → {seq_prefix}")
    creadas += 1

env.cr.commit()
print(f"\n✓ Secuencias creadas/asignadas: {creadas} | Ya tenían: {ya_tenia}")
