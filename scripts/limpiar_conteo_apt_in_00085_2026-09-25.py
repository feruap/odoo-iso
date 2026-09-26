# APT/IN/00085 quedo con el conteo prellenado en 35 porque la reserva
# automatica de Odoo lo reescribio (ver StockMove._action_assign en
# amunet_woocommerce 19.0.19.4.0). Se regresa a cero para que Almacen cuente.
p = env['stock.picking'].search([('name', '=', 'APT/IN/00085')], limit=1)
assert p and p.state != 'done', 'APT/IN/00085 no esta pendiente'
print('antes  : estado=%s  conteo=%s'
      % (p.state, sum(p.move_ids.move_line_ids.mapped('quantity'))))
p.move_ids.move_line_ids.sudo().write({'quantity': 0.0})
env.cr.commit()
p.invalidate_recordset()
print('despues: estado=%s  conteo=%s  (entregado por Produccion: %s)'
      % (p.state, sum(p.move_ids.move_line_ids.mapped('quantity')),
         sum(p.move_ids.move_line_ids.mapped('qty_demanded'))))

print()
print('--- las dos entregas pendientes de %s ---' % 'APT')
for e in env['amunet.entrega.pt'].search([('production_id', '=', 140)], order='id'):
    pk = e.picking_ingreso_id
    print('  entrega id=%-3s entregado=%-6s doc=%-14s estado=%-10s conteo capturado=%s'
          % (e.id, e.quantity_delivered, pk.name, pk.state,
             sum(pk.move_ids.move_line_ids.mapped('quantity'))))
