# Caducidad correcta del cartucho MPCAC08 (recepcion AMP/IN/00190): julio 2030.
# Estaba en 2026-07-16 (fecha de recepcion). Se usa dia 01 por convencion de los
# otros lotes (YYYY-MM-01). Autorizado por Fernando 2026-07-16.
from datetime import datetime
Lot = env['stock.lot'].sudo()
prod = env['product.product'].search([('default_code', '=', 'MPCAC08')], limit=1)
nueva = datetime(2030, 7, 1)
for name in ('CAC08072601', 'CAC08072602'):
    lot = Lot.search([('product_id', '=', prod.id), ('name', '=', name)], limit=1)
    if not lot:
        print('SIN lote:', name); continue
    antes = lot.expiration_date
    lot.expiration_date = nueva
    print('%s: %s -> %s' % (name, antes, lot.expiration_date))
env.cr.commit()
