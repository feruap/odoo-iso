# Las 5 recepciones de liberacion (AMP/IN/00223-00227) quedaron con el HEADER
# apuntando a AMP/Existencias (correcto) pero el MOVE re-enrutado a Control de
# calidad por el action_confirm de amunet_recepcion_materiales (re-quarantina
# incoming de productos con cuarentena, sin distinguir liberaciones de QC).
# Se corrige el destino del move + move_line a AMP/Existencias para que Almacen
# valide y el material aterrice en Existencias. Autorizado por Fernando 2026-07-22.
Picking = env['stock.picking'].sudo()
wh = env['stock.warehouse'].sudo().search([('code', '=', 'AMP')], limit=1)
dest = wh.lot_stock_id  # AMP/Existencias
names = ['AMP/IN/00223', 'AMP/IN/00224', 'AMP/IN/00225', 'AMP/IN/00226', 'AMP/IN/00227']
for name in names:
    p = Picking.search([('name', '=', name)], limit=1)
    if not p:
        print('no existe', name); continue
    lotes = set(p.move_line_ids.mapped('lot_id.name'))
    p.move_ids.write({'location_dest_id': dest.id})
    p.move_line_ids.write({'location_dest_id': dest.id})
    print(name, '| lotes', lotes, '-> destino', dest.complete_name, '| estado', p.state)
env.cr.commit()
print('LISTO')
