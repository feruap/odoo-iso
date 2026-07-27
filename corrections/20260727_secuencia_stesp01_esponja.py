"""
Crea secuencia Amunet para STESP01 (Esponja para toma de muestra).
Prefijo: ESP01%(month)s%(y)s (quita primeros 2 chars 'ST' → 'ESP01').
"""
tmpl = env['product.template'].with_context(active_test=False).search([
    ('default_code', '=', 'STESP01')
], limit=1)
if not tmpl:
    print("ERROR: STESP01 no encontrado")
else:
    prod = tmpl.product_variant_ids[:1]
    prefix_base = 'ESP01'
    seq_code   = f'amunet.lot.{prefix_base}.{tmpl.id}'
    seq_prefix = f'{prefix_base}%(month)s%(y)s'

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
    env.cr.commit()
    print(f"[{tmpl.default_code}] {tmpl.name} → secuencia {seq_prefix}01 ✓")
