# Caducidad del vial STBPR01 (recepcion AMP/IN/00191): mayo 2028. Estaba vacia.
# Dia 01 por convencion. Autorizado por Fernando 2026-07-16.
from datetime import datetime
Lot = env['stock.lot'].sudo()
prod = env['product.product'].search([('default_code', '=', 'STBPR01')], limit=1)
lot = Lot.search([('product_id', '=', prod.id), ('name', '=', 'BPR01072601')], limit=1)
if lot:
    antes = lot.expiration_date
    lot.expiration_date = datetime(2028, 5, 1)
    print('STBPR01/BPR01072601: %s -> %s' % (antes, lot.expiration_date))
    env.cr.commit()
else:
    print('SIN lote STBPR01/BPR01072601')
