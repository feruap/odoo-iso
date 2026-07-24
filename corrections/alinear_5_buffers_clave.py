# Alinea la secuencia de lote de los 5 buffers que usaban codigo de funcion
# (SSP/APB/TRE) al prefijo = clave sin las 2 primeras letras "ST". Solo afecta
# lotes FUTUROS; los lotes existentes conservan su nombre (trazabilidad). Tambien
# resuelve la colision STBDN01/SPAPB01 (ambos usaban APB01). Autorizado por
# Fernando 2026-07-22.
Tmpl = env['product.template'].sudo()
codes = ['STBAC01', 'STBCH01', 'STBDN01', 'STBTR01', 'STBTR02']
for code in codes:
    t = Tmpl.search([('default_code', '=', code)], limit=1)
    if not t:
        print('OJO no existe', code); continue
    t.amunet_lot_prefix = code[2:]  # BAC01, BCH01, BDN01, BTR01, BTR02
    print('%s -> secuencia %s' % (code, t.lot_sequence_id.prefix))

env.cr.commit()

for code in codes:
    p = env['product.product'].sudo().search([('default_code', '=', code)], limit=1)
    print('  %s -> proximo lote: %s' % (code, p._amunet_next_lot_names(1)))
print('LISTO')
