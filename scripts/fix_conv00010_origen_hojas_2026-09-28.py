# CONV/00010 (separacion de 30 combos Zika/Chikungunya) no se podia validar:
# las tres hojas maestras tenian el MISMO origen que destino
# (AMP/Entrada/Control de calidad -> AMP/Entrada/Control de calidad).
#
# QUE PASO: los movimientos nacieron bien el 17-sep
# (Conversion de combos -> Control de calidad). El 25-sep Karla edito el
# encabezado del traslado y, al guardar, Odoo propago el location_id del
# ENCABEZADO a las lineas. En esta recepcion el combo aterrizo en Control de
# calidad, asi que el origen pisado quedo igual al destino. El movimiento del
# combo, que no se toco, conserva sus ubicaciones correctas.
#
# En CONV/00006 a 00009 pasa lo mismo, pero ahi el combo aterrizo en
# AMP/Entrada, distinto del destino, y por eso validaron sin problema.
#
# Se restaura el origen de las tres hojas a la ubicacion virtual de conversion.
PICKING = 'CONV/00010'
HOJAS = ('SPHMC86', 'SPHMC87', 'SPHMC88')

p = env['stock.picking'].sudo().search([('name', '=', PICKING)], limit=1)
assert p, 'no existe %s' % PICKING
assert p.state not in ('done', 'cancel'), 'el traslado esta en %s' % p.state

virtual = p._amunet_combo_virtual_location()
assert virtual, 'no se resolvio la ubicacion virtual de conversion'

print('=== antes ===')
for m in p.move_ids.sorted('id'):
    print('  %-10s %-34s -> %s' % (m.product_id.default_code,
          m.location_id.complete_name[:34], m.location_dest_id.complete_name[:34]))

hojas = p.move_ids.filtered(lambda m: m.product_id.default_code in HOJAS)
assert len(hojas) == 3, 'se esperaban 3 hojas, hay %s' % len(hojas)
for m in hojas:
    if m.location_id == virtual:
        print('  %s ya tenia el origen correcto, no se toca' % m.product_id.default_code)
        continue
    assert m.location_id == m.location_dest_id, \
        ('%s no tiene origen igual a destino ni es el virtual (%s -> %s): '
         'revisar a mano antes de tocar'
         % (m.product_id.default_code, m.location_id.complete_name,
            m.location_dest_id.complete_name))
    m.write({'location_id': virtual.id})
    m.move_line_ids.write({'location_id': virtual.id})

env.cr.commit()
p.invalidate_recordset()

print()
print('=== despues ===')
for m in p.move_ids.sorted('id'):
    ok = 'ok' if m.location_id != m.location_dest_id else 'SIGUE MAL'
    print('  %-10s %-34s -> %-34s [%s]' % (m.product_id.default_code,
          m.location_id.complete_name[:34], m.location_dest_id.complete_name[:34], ok))
print()
print('  estado del traslado: %s' % p.state)

# ---------------------------------------------------------------------------
# SEGUNDA PARTE: recrear las lineas de detalle que se borraron.
#
# Al editar el encabezado tambien desaparecieron las lineas de las tres hojas
# ("las lineas de las hojas maestras desaparecieron de la pantalla", Karla).
# Los LOTES que la conversion creo el 17-sep sobrevivieron intactos, vacios y
# sin analisis de Calidad:
#     SPHMC86 -> HMC86092601     SPHMC87 -> HMC87092601
#     SPHMC88 -> HMC88092601     (los tres, lote de fabrica I16326080003)
#
# Se recrean las lineas apuntando a ESOS lotes y no a lotes nuevos: el propio
# modulo documenta por que -dos lotes para el mismo material fisico parten el
# inventario y dejan huerfano al analisis de Calidad-.
LOTES = {'SPHMC86': 'HMC86092601', 'SPHMC87': 'HMC87092601', 'SPHMC88': 'HMC88092601'}

p = env['stock.picking'].sudo().search([('name', '=', PICKING)], limit=1)
virtual = p._amunet_combo_virtual_location()
print()
print('=== recreando las lineas de detalle ===')
for m in p.move_ids.filtered(lambda x: x.product_id.default_code in LOTES):
    if m.move_line_ids:
        print('  %-10s ya tiene %s linea(s), no se toca' % (m.product_id.default_code, len(m.move_line_ids)))
        continue
    lote = env['stock.lot'].sudo().search([
        ('name', '=', LOTES[m.product_id.default_code]),
        ('product_id', '=', m.product_id.id)], limit=1)
    assert lote, 'no se encontro el lote %s' % LOTES[m.product_id.default_code]
    env['stock.move.line'].sudo().create({
        'move_id': m.id, 'picking_id': p.id,
        'product_id': m.product_id.id, 'product_uom_id': m.product_uom.id,
        'lot_id': lote.id, 'quantity': m.product_uom_qty,
        'location_id': virtual.id, 'location_dest_id': m.location_dest_id.id,
        'company_id': m.company_id.id,
    })
    print('  %-10s linea creada: %s pz  lote %s' % (m.product_id.default_code,
                                                    m.product_uom_qty, lote.name))
env.cr.commit()

p.invalidate_recordset()
print()
print('=== como queda CONV/00010 ===')
for m in p.move_ids.sorted('id'):
    lot = ', '.join(m.move_line_ids.mapped('lot_id.name')) or '-'
    print('  %-10s %-8s %-30s -> %-30s lote=%s' % (
        m.product_id.default_code, m.product_uom_qty,
        m.location_id.complete_name[:30], m.location_dest_id.complete_name[:30], lot))
print('  estado: %s' % p.state)
