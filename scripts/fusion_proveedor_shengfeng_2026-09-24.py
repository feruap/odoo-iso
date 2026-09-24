# Habia DOS fichas del mismo proveedor, separadas por una "s" y un espacio:
#   id 504  "Cangzhou ShengFeng Plastic Product Co., Ltd."   (mayo-2026)
#   id 556  "Cangzhou Shengfeng Plastic Products Co.,Ltd."   (agosto-2026)
#
# Todo el mapeo de claves se cargo sobre la 504, asi que los 8 productos que
# colgaban de la 556 nunca iban a recibir clave: COENV12-16 y los cartuchos
# MPCAR77 (Transglutaminasa), MPCAR78 (HPV E7) y MPCAR79 (CARBA 5 en 1).
#
# La 556 no tiene NINGUNA operacion: 0 ordenes de compra, 0 recepciones,
# 0 facturas. Solo los 8 renglones de producto. Por eso se puede traspasar y
# archivar sin arrastrar historial ni romper trazabilidad; y por eso NO hace
# falta el asistente de fusion de contactos de Odoo, que es mucho mas invasivo.
#
# Se ARCHIVA, no se borra: si algun dia aparece un documento viejo que la
# referencie, el registro sigue ahi.

BUENA, DUPLICADA = 504, 556

S = env['product.supplierinfo']
P = env['res.partner']
buena, dup = P.browse(BUENA), P.browse(DUPLICADA)
assert buena.exists() and dup.exists(), 'falta alguna de las dos fichas'
print('buena     : %s' % buena.name)
print('duplicada : %s' % dup.name)

# resguardo: la duplicada no debe tener operaciones
for modelo, campo in [('purchase.order','partner_id'), ('stock.picking','partner_id'),
                      ('account.move','partner_id')]:
    n = env[modelo].search_count([(campo, '=', dup.id)])
    assert n == 0, 'la ficha duplicada tiene %s registros en %s: no traspasar' % (n, modelo)
print('sin operaciones en la duplicada: se puede traspasar\n')

lineas = S.search([('partner_id', '=', dup.id)])
print('=== TRASPASO DE %s RENGLONES ===' % len(lineas))
for si in lineas:
    t = si.product_tmpl_id
    ya = S.search_count([('product_tmpl_id', '=', t.id), ('partner_id', '=', buena.id)])
    assert ya == 0, '%s ya tiene renglon en la ficha buena: revisar a mano' % t.default_code
    si.partner_id = buena.id
    print('  %-9s %-34s -> ficha %s' % (t.default_code, (t.name or '')[:34], buena.id))

dup.active = False
env.cr.commit()

print('\n=== COMO QUEDA ===')
for p in P.with_context(active_test=False).search([('name', 'ilike', 'shengfeng')]):
    print('  id %-4s activo=%-3s renglones=%-4s %s'
          % (p.id, 'si' if p.active else 'NO',
             S.search_count([('partner_id', '=', p.id)]), p.name))
print('\nLos 8 traspasados siguen SIN clave de ShengFeng: hay que mapearlos.')
for si in S.search([('partner_id', '=', buena.id)]).filtered(
        lambda s: s.product_tmpl_id.default_code in
        ('COENV12','COENV13','COENV14','COENV15','COENV16','MPCAR77','MPCAR78','MPCAR79')):
    print('  %-9s %s' % (si.product_tmpl_id.default_code,
                         si.product_code or '(sin clave)'))
