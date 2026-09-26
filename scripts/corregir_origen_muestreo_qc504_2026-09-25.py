# El muestreo de QC/2026/00504 salio de APT/Entrada (las 35 ya entregadas del
# parcial) en vez de APT/Almacen Temporal PT (las 30 que este analisis ampara).
# Causa: _get_source_location con search(limit=1) sin orden -- ya corregido en
# amunet_quality 19.0.3.61.0. Aqui se repara el inventario que quedo movido.
#
# Estado actual        ->  como debe quedar
#   Temporal PT     30 ->  25   (30 - 10 muestreadas + 5 devueltas)
#   APT/Entrada     25 ->  35   (nunca debio perder las 10)
#   Control calidad  5 ->   0   (se devuelven al Temporal, de donde salieron)
#   Desechos        10 ->  10   (5 del parcial + 5 de este)
QC_ID = 931
q = env['amunet.quality.check'].browse(QC_ID)
lote, prod = q.lot_id, q.product_id
L = env['stock.location']
temporal = L.search([('complete_name', '=', 'APT/Almacén Temporal PT')], limit=1)
entrada = L.search([('complete_name', '=', 'APT/Entrada')], limit=1)
calidad = q._get_quality_control_location()
assert temporal and entrada and calidad

def stock(loc):
    return sum(env['stock.quant'].sudo().search([
        ('lot_id', '=', lote.id), ('location_id', '=', loc.id)]).mapped('quantity'))

def foto(titulo):
    print('%s Temporal=%s  Entrada=%s  Calidad=%s'
          % (titulo, stock(temporal), stock(entrada), stock(calidad)))

foto('ANTES :')

# --- 1. La devolucion de la muestra regresa al Temporal, no a Entrada --------
dev = env['stock.picking'].search([('origin', 'ilike', q.name),
                                   ('state', 'not in', ('done', 'cancel'))])
for p in dev:
    print('\n  redirigiendo %s: %s -> %s'
          % (p.name, p.location_dest_id.complete_name, temporal.complete_name))
    p.write({'location_dest_id': temporal.id})
    p.move_ids.write({'location_dest_id': temporal.id})
    if p.state in ('confirmed', 'waiting'):
        p.action_assign()
    for m in p.move_ids:
        m.quantity = m.product_uom_qty
        m.picked = True
        for ml in m.move_line_ids:
            ml.write({'location_dest_id': temporal.id, 'lot_id': lote.id,
                      'quantity': m.product_uom_qty, 'picked': True})
    p.with_context(skip_backorder=True, picking_label_report=False).button_validate()
    print('  %s validada (%s)' % (p.name, p.state))

# --- 2. Reponer a Entrada las 10 que el muestreo le quito de mas -------------
tipo = env['stock.picking.type'].search([('code', '=', 'internal'),
                                         ('company_id', '=', q.company_id.id)], limit=1)
corr = env['stock.picking'].create({
    'picking_type_id': tipo.id,
    'location_id': temporal.id,
    'location_dest_id': entrada.id,
    'origin': 'Correccion origen de muestreo %s' % q.name,
    'move_ids': [(0, 0, {
        'product_id': prod.id,
        'product_uom_qty': 10.0,
        'product_uom': prod.uom_id.id,
        'location_id': temporal.id,
        'location_dest_id': entrada.id,
        'procure_method': 'make_to_stock',
        'company_id': q.company_id.id,
    })],
})
corr.action_confirm()
corr.action_assign()
for m in corr.move_ids:
    m.move_line_ids.unlink()
    env['stock.move.line'].create({
        'picking_id': corr.id, 'move_id': m.id, 'product_id': prod.id,
        'product_uom_id': prod.uom_id.id, 'location_id': temporal.id,
        'location_dest_id': entrada.id, 'lot_id': lote.id,
        'quantity': 10.0, 'picked': True, 'company_id': q.company_id.id,
    })
    m.picked = True
corr.with_context(skip_backorder=True, picking_label_report=False).button_validate()
print('\n  %s validada: 10 pz Temporal -> Entrada (%s)' % (corr.name, corr.state))

env.cr.commit()
print()
foto('DESPUES:')
tot = sum(s.quantity for s in env['stock.quant'].sudo().search([('lot_id', '=', lote.id)])
          if s.location_id.usage == 'internal')
print('TOTAL FISICO INTERNO: %s' % tot)
