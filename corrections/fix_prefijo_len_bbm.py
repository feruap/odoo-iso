# Corrige prefijos de lote:
# - LEN01 (Lengueta): secuencia tenia "DSC01" (de Desecante, error) -> "LEN01"
#   (coincide con su lote real LEN01042601; LEN01 es codigo no estandar, prefijo
#   = clave completa).
# - STBBM01/02 (buffers PCR rapida): compartian el prefijo "BMB01" (typo, deberia
#   ser BBM por la clave STBBM). Son productos DISTINTOS -> STBBM01=BBM01,
#   STBBM02=BBM02 (coincide con sus lotes reales BBM01*/BBM02* y evita compartir
#   contador). Autorizado por Fernando 2026-07-22.
Tmpl = env['product.template'].sudo()

fixes = [('LEN01', 'LEN01'), ('STBBM01', 'BBM01'), ('STBBM02', 'BBM02')]
for code, prefijo in fixes:
    t = Tmpl.search([('default_code', '=', code)], limit=1)
    if not t:
        print('OJO no existe', code); continue
    t.amunet_lot_prefix = prefijo
    print('%s -> secuencia %s' % (code, t.lot_sequence_id.prefix))

env.cr.commit()

for code in ['LEN01', 'STBBM01', 'STBBM02']:
    p = env['product.product'].sudo().search([('default_code', '=', code)], limit=1)
    print('  %s -> proximo lote: %s' % (code, p._amunet_next_lot_names(1)))
print('LISTO')
