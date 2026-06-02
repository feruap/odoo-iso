"""Asignar secuencias de lote Amunet a COENV12-COENV16.

COENV12 al COENV16 fueron creados sin la secuencia amunet.lot.* que tienen sus
homólogos COENV01-11. Este script crea las secuencias faltantes y las vincula.
Es idempotente: si la secuencia ya existe, solo vincula.
"""

productos = [
    {'code': 'COENV12', 'prefix_code': 'ENV12'},
    {'code': 'COENV13', 'prefix_code': 'ENV13'},
    {'code': 'COENV14', 'prefix_code': 'ENV14'},
    {'code': 'COENV15', 'prefix_code': 'ENV15'},
    {'code': 'COENV16', 'prefix_code': 'ENV16'},
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
