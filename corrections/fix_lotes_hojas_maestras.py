# Correccion de lote mal codificado en AMP/IN/00189 (16-jul-2026):
# SPHMC75 y SPHMC76 quedaron con el lote HMC53072601 (copiado de SPHMC53).
# Por la convencion (clave sin las 2 primeras letras + MMAANN) deben ser
# HMC75072601 y HMC76072601. Solo se renombra el registro de lote de CADA
# producto; el lote HMC53072601 de SPHMC53 NO se toca. La caducidad la revisa
# Fernando aparte. Autorizado por Fernando 2026-07-16.
Lot = env['stock.lot'].sudo()
Prod = env['product.product']
fixes = [
    ('SPHMC75', 'HMC53072601', 'HMC75072601'),
    ('SPHMC76', 'HMC53072601', 'HMC76072601'),
]
for code, old, new in fixes:
    prod = Prod.search([('default_code', '=', code)], limit=1)
    if not prod:
        print('SIN producto:', code); continue
    lot = Lot.search([('product_id', '=', prod.id), ('name', '=', old)], limit=1)
    if not lot:
        print('SIN lote:', code, old); continue
    # verificar que no exista ya el nuevo nombre para ese producto
    if Lot.search_count([('product_id', '=', prod.id), ('name', '=', new)]):
        print('COLISION, no renombro:', code, new); continue
    lot.name = new
    print('renombrado:', code, old, '->', new)
env.cr.commit()
# verificacion
for code, old, new in fixes:
    prod = Prod.search([('default_code', '=', code)], limit=1)
    n = Lot.search_count([('product_id', '=', prod.id), ('name', '=', new)])
    print('verif %s tiene %s:' % (code, new), n)
