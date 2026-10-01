# 0926/01/CCF: Almacen surtio el buffer en DOS lotes (Mery, 1-oct-2026):
# el grande y 215 piezas del BTR01032601. El sistema los tenia partidos en
# 210 + 5 porque al dar de baja el BTR122502 completo con lo que encontro.
mo = env['mrp.production'].search([('name', '=', '0926/01/CCF')])
destino = env['stock.lot'].search([('name', '=', 'BTR01032601'),
                                   ('product_id', '=', 837)], limit=1)
lineas = mo.move_raw_ids.move_line_ids.filtered(
    lambda l: l.product_id.id == 837 and l.lot_id != destino and l.quantity < 1000)
for l in lineas:
    print('pasar %s piezas de %s a %s' % (l.quantity, l.lot_id.name, destino.name))
    l.sudo().with_context(amunet_supply_internal=True).write({'lot_id': destino.id})

# juntar los renglones que quedaron del mismo lote
mismas = mo.move_raw_ids.move_line_ids.filtered(
    lambda l: l.product_id.id == 837 and l.lot_id == destino)
if len(mismas) > 1:
    total = sum(x.quantity for x in mismas)
    mismas[0].sudo().with_context(amunet_supply_internal=True).write({'quantity': total})
    for extra in mismas[1:]:
        extra.sudo().with_context(amunet_supply_internal=True).unlink()
    print('juntados en un solo renglon de', total)

mo.message_post(body=(
    'El buffer queda en los <b>dos lotes que surtio Almacen</b>: el BTR02082601 '
    'y 215 piezas del BTR01032601. Estaban partidos en 210 + 5 porque al darse '
    'de baja el lote BTR122502 el sistema completo la diferencia con lo que '
    'encontro.<br/><br/>'
    'Queda dicho para el registro: esas 215 piezas del BTR01032601 caducan el '
    '30.09.28, menos de dos anios. Se dejan porque es lo que Almacen entrego '
    'fisicamente.'))
env.cr.commit()
print()
print('=== buffer en la orden ===')
for l in mo.move_raw_ids.move_line_ids.filtered(lambda x: x.product_id.id == 837):
    print('   %-13s %-12s %9s' % (l.lot_id.name, l.lot_id.expiration_date.date(), l.quantity))
