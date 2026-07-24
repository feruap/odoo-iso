# AMP/IN/00213: caducidad 4 anos desde hoy (2026-07-20 -> 2030-07-20) en las 6
# lineas de cartuchos. Autorizado por Fernando 2026-07-20.
p = env['stock.picking'].search([('name','=','AMP/IN/00213')], limit=1)
assert p and p.state=='assigned', 'picking inesperado'
CAD = '2030-07-20 09:00:00'
for move in p.move_ids:
    for ml in move.move_line_ids:
        ml.write({'expiration_date': CAD})
        if ml.lot_id:
            ml.lot_id.sudo().write({'expiration_date': CAD})
    move.write({'amunet_exp_date': '20/07/2030'})
env.cr.commit()
for ml in p.move_line_ids:
    print(ml.product_id.default_code, '| lote', ml.lot_name, '| cad', ml.expiration_date)
