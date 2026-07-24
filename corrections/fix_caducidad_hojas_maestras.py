# Caducidad de las hojas maestras SPHMC75/76 (recepcion AMP/IN/00189): mayo 2028.
# Estaba en 2026-07-16 (fecha de recepcion). Dia 01 por convencion. Autorizado
# por Fernando 2026-07-16.
from datetime import datetime
Lot = env['stock.lot'].sudo()
Prod = env['product.product']
nueva = datetime(2028, 5, 1)
for code, name in [('SPHMC75', 'HMC75072601'), ('SPHMC76', 'HMC76072601')]:
    prod = Prod.search([('default_code', '=', code)], limit=1)
    lot = Lot.search([('product_id', '=', prod.id), ('name', '=', name)], limit=1)
    if not lot:
        print('SIN lote:', code, name); continue
    antes = lot.expiration_date
    lot.expiration_date = nueva
    print('%s/%s: %s -> %s' % (code, name, antes, lot.expiration_date))
env.cr.commit()
