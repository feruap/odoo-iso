"""Asignar secuencias de lote Amunet a STBPR04, STHIE04 y STVAS01.

Estos tres semiterminados fueron creados sin la secuencia amunet.lot.*
que tienen sus homólogos de la misma familia. Este script crea las
secuencias faltantes y las vincula. Es idempotente.
"""

productos = [
    {'code': 'STBPR04', 'prefix_code': 'BPR04'},
    {'code': 'STHIE04', 'prefix_code': 'HIE04'},
    {'code': 'STVAS01', 'prefix_code': 'VAS01'},
]

for p in productos:
    pt = env['product.template'].sudo().search(
        [('default_code', '=', p['code']), ('active', '=', True)], limit=1
    )
    if not pt:
        print(f"[NO ENCONTRADO] {p['code']}")
        continue

    seq_code = f"amunet.lot.{p['prefix_code']}.{pt.id}"
    seq_prefix = f"{p['prefix_code']}%(month)s%(y)s"

    seq = env['ir.sequence'].sudo().search([('code', '=', seq_code)], limit=1)
    if not seq:
        seq = env['ir.sequence'].sudo().create({
            'name': f"Lote {p['code']} - Amunet",
            'code': seq_code,
            'prefix': seq_prefix,
            'padding': 2,
            'number_increment': 1,
            'number_next': 1,
            'implementation': 'standard',
            'active': True,
            'company_id': False,
        })
        print(f"[CREADA] {seq_code} → prefijo: {seq_prefix}")
    else:
        print(f"[YA EXISTE] {seq_code}")

    pt.write({'lot_sequence_id': seq.id})
    print(f"  → Vinculada a {p['code']} (id={pt.id}): {pt.name}")

env.cr.commit()
print("Listo.")
