# Completa AMP/IN/00197: proveedor Hangzhou Tongzhou, lote proveedor D00026060039
# (ambas hojas), caducidad 2028-05-01. Autorizado por Fernando 2026-07-20.
p = env['stock.picking'].search([('name','=','AMP/IN/00197')], limit=1)
assert p and p.state=='assigned', 'picking inesperado'
p.write({'partner_id': 321})
for move in p.move_ids:
    for ml in move.move_line_ids:
        ml.write({'expiration_date': '2028-05-01 09:00:00'})
        if ml.lot_id:
            ml.lot_id.sudo().write({'expiration_date': '2028-05-01 09:00:00'})
    move.write({'amunet_supplier_lot': 'D00026060039', 'amunet_exp_date': '01/05/2028'})
env.cr.commit()
for ml in p.move_line_ids:
    print(ml.product_id.default_code, '| lote', ml.lot_name, '| prov', ml.factory_lot_id.name, '| cad', ml.expiration_date)
print('Proveedor:', p.partner_id.name)
