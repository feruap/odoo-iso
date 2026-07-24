# Revierte la caducidad de AMP/IN/00213 a los valores originales (yo los pise con
# 2030-07-20). Los 5 reales vuelven a 2030-07-01; MPCAR32 a su default original.
# Autorizado por Fernando 2026-07-20.
# move_id: (line_id, lot_id)
reales = {5712:(6218,1954), 5714:(6220,1956), 5715:(6221,1957), 5711:(6217,1953), 5710:(6216,1952)}
CAD = '2030-07-01 15:00:00'
for move_id, (line_id, lot_id) in reales.items():
    env['stock.move'].browse(move_id).write({'amunet_exp_date': '01.07.2030'})
    env['stock.move.line'].browse(line_id).write({'expiration_date': CAD})
    env['stock.lot'].sudo().browse(lot_id).write({'expiration_date': CAD})
# MPCAR32 (linea nueva del swap): vuelve a su original (sin caducidad real)
env['stock.move'].browse(5736).write({'amunet_exp_date': False})
env['stock.move.line'].browse(6242).write({'expiration_date': '2026-07-20 18:04:52'})
env['stock.lot'].sudo().browse(1960).write({'expiration_date': '2026-07-20 18:04:52'})
env.cr.commit()
p = env['stock.picking'].search([('name','=','AMP/IN/00213')], limit=1)
for ml in p.move_line_ids.sorted(lambda l: l.product_id.default_code):
    print(ml.product_id.default_code, '| cad', ml.expiration_date, '| mfg', ml.move_id.amunet_mfg_date)
