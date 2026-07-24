# AMP/QC/00369 (955): manda los 3 EPP (cofia + guantes) de Entrada a Existencias,
# saltando Control de calidad (son EPP, no requieren analisis). Autorizado Fernando.
p = env['stock.picking'].browse(955)
assert p.name == 'AMP/QC/00369', 'picking inesperado'
STOCK = 5  # AMP/Existencias
for move in p.move_ids:
    move.location_dest_id = STOCK
    for ml in move.move_line_ids:
        ml.location_dest_id = STOCK
res = p.button_validate()
print('validate:', 'wizard:'+res.get('res_model') if isinstance(res, dict) else res)
print('estado picking:', p.state)
for code in ['COCOF01','COGEC01','COGME01']:
    q = env['stock.quant'].sudo().search([('product_id.default_code','=',code),('location_id','=',STOCK),('quantity','>',0)])
    print(code, '-> Existencias:', sum(q.mapped('quantity')))
# verificar que NO se creo un analisis por error
qc = env['amunet.quality.check'].search([('lot_id','in', p.move_line_ids.mapped('lot_id').ids)]) if p.move_line_ids.mapped('lot_id') else env['amunet.quality.check']
print('QC creados (debe ser 0):', len(qc))
env.cr.commit()
