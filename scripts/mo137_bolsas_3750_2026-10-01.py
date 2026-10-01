# 0926/01/CCF: la linea de bolsas decia 3,750 surtido pero solo 3,600 en el
# lote. Faltaban 150 y no habia de donde: el lote BOL01072501 estaba 100%
# comprometido, y 4,408 piezas las tenian apartadas dos ordenes que no se han
# surtido (1026/01/VID y 1026/01/CRD, arrancan el 2 y el 5 de octubre).
# Soltada esa reserva, ya alcanza.
mo = env['mrp.production'].search([('name', '=', '0926/01/CCF')])
mov = mo.move_raw_ids.filtered(lambda m: m.product_id.default_code == 'MPBOL01')
linea = mov.move_line_ids
print('antes: lote %s con %s, surtido %s' % (
    linea.lot_id.name, linea.quantity, mov.amunet_qty_supplied))
linea.sudo().with_context(amunet_supply_internal=True).write({'quantity': 3750.0})
mov.sudo().with_context(amunet_supply_internal=True).write({'quantity': 3750.0})
mo.message_post(body=(
    'La linea de <b>bolsas</b> queda completa: 3,750 en el lote BOL01072501, '
    'igual que la cantidad surtida. Faltaban 150 y no habia de donde sacarlas '
    'porque el lote estaba comprometido al 100%: 4,408 piezas las tenian '
    'apartadas dos ordenes que todavia no se surten (1026/01/VID y 1026/01/CRD). '
    'Se solto esa reserva, que era automatica y no material entregado.'))
env.cr.commit()
print('ahora: lote %s con %s' % (linea.lot_id.name, linea.quantity))
print()
print('=== la orden completa ===')
for l in mo.move_raw_ids.move_line_ids.sorted(
        lambda x: (x.product_id.default_code or '', x.lot_id.name or '')):
    cad = l.lot_id.expiration_date
    print('   %-9s %-13s %-12s %9s' % (
        l.product_id.default_code, l.lot_id.name or '-',
        cad.date() if cad else 'sin caducidad', l.quantity))
