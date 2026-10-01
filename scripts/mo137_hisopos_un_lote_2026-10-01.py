# 0926/01/CCF: los 150 hisopos que el sistema habia tomado del HIS01082601
# vuelven al HIS01012601, que es el que surtio Almacen. Antes no se podia:
# en Fabrica solo habia 1,462 piezas de ese lote y la orden ya tenia 3,600
# apartadas. Con el traspaso AMPB/INT/00083 (10,000 piezas de Burgos,
# validado hoy 17:25) hay 7,862 libres y ya alcanza.
# Caducidad del HIS01012601: 30.11.28, pasa los dos anios.
mo = env['mrp.production'].search([('name', '=', '0926/01/CCF')])
destino = env['stock.lot'].search([('name', '=', 'HIS01012601')], limit=1)
lineas = mo.move_raw_ids.move_line_ids.filtered(
    lambda l: l.product_id.default_code == 'STHIS01' and l.lot_id != destino)
for l in lineas:
    print('pasar %s hisopos de %s a %s' % (l.quantity, l.lot_id.name, destino.name))
    l.sudo().with_context(amunet_supply_internal=True).write({'lot_id': destino.id})
mismas = mo.move_raw_ids.move_line_ids.filtered(
    lambda l: l.product_id.default_code == 'STHIS01')
if len(mismas) > 1:
    total = sum(x.quantity for x in mismas)
    mismas[0].sudo().with_context(amunet_supply_internal=True).write({'quantity': total})
    for extra in mismas[1:]:
        extra.sudo().with_context(amunet_supply_internal=True).unlink()
    print('juntados en un solo renglon de', total)
mo.message_post(body=(
    'Los hisopos quedan en un solo lote, el <b>HIS01012601</b> que surtio '
    'Almacen. Los 150 que el sistema habia tomado de otro lote vuelven a este. '
    'Se pudo gracias al traspaso <b>AMPB/INT/00083</b> validado hoy: entraron '
    '10,000 piezas de Burgos a Fabrica, donde antes solo habia 1,462 de ese lote '
    'contra 3,600 ya apartadas para esta orden.'))
env.cr.commit()
print()
print('=== la orden completa ===')
for l in mo.move_raw_ids.move_line_ids.sorted(
        lambda x: (x.product_id.default_code or '', x.lot_id.name or '')):
    cad = l.lot_id.expiration_date
    print('   %-9s %-13s %-12s %9s' % (
        l.product_id.default_code, l.lot_id.name or '-',
        cad.date() if cad else 'sin caducidad', l.quantity))
