# La prueba de VITAMINET D (DMVID01) usa la bolsa de 8x13 (MPBOL03), no la de
# 6x12 (MPBOL01). (Mery, 2-oct-2026)
#
# Se corrige en los dos lados:
#   1. La RECETA (BoM 56), para todas las ordenes futuras.
#   2. La orden ABIERTA 1026/01/VID, que ya tenia 940 bolsas de la equivocada.
#
# Se puede cambiar sin devolver nada: el material sigue en AMP/Existencias,
# Produccion todavia no firma que lo recibio, asi que no bajo al piso.
CTX = {'amunet_supply_internal': True}
vieja = env['product.product'].search([('default_code', '=', 'MPBOL01')], limit=1)
nueva = env['product.product'].search([('default_code', '=', 'MPBOL03')], limit=1)

print('=== 1) la receta (BoM 56) ===')
linea = env['mrp.bom.line'].sudo().search([
    ('bom_id', '=', 56), ('product_id', '=', vieja.id)])
for l in linea:
    print('   antes:', l.product_id.default_code, l.product_id.name)
    l.write({'product_id': nueva.id, 'product_uom_id': nueva.uom_id.id})
    print('   ahora:', l.product_id.default_code, l.product_id.name)

print()
print('=== 2) la orden 1026/01/VID ===')
mo = env['mrp.production'].browse(167)
mov = mo.move_raw_ids.filtered(lambda m: m.product_id == vieja)
for m in mov:
    surtido = m.amunet_qty_supplied
    print('   antes:', m.product_id.default_code, '| requerido', m.product_uom_qty,
          '| surtido', surtido, '| lote', m.move_line_ids.mapped('lot_id.name'))
    m.sudo()._do_unreserve()
    m.sudo().with_context(**CTX).write({
        'product_id': nueva.id,
        'product_uom': nueva.uom_id.id,
        'amunet_lot_id': False,
        'amunet_qty_supplied': surtido,
    })
    m.sudo()._action_assign()
    m.invalidate_recordset()
    print('   ahora:', m.product_id.default_code, '| requerido', m.product_uom_qty,
          '| surtido', m.amunet_qty_supplied, '| lote', m.move_line_ids.mapped('lot_id.name'))

mo.message_post(body=(
    'Corregida la <b>bolsa</b>: esta prueba usa la termosellable de <b>8x13 cm '
    '(MPBOL03)</b>, no la de 6x12 (MPBOL01). Se cambio en esta orden y tambien '
    'en la receta, para las que vengan. Se pudo cambiar sin devolver nada '
    'porque el material seguia en el anaquel: Produccion aun no firmaba que lo '
    'recibio. <b>Almacen tiene que surtir la bolsa correcta.</b>'))
env.cr.commit()

print()
print('=== como queda la orden ===')
for m in mo.move_raw_ids.sorted(lambda x: x.product_id.default_code or ''):
    print('   %-9s %-30s %8s  lotes: %s' % (
        m.product_id.default_code, (m.product_id.name or '')[:30],
        m.product_uom_qty, m.move_line_ids.mapped('lot_id.name') or '-'))
print()
print('=== y la receta ===')
for l in env['mrp.bom'].browse(56).bom_line_ids.sorted(lambda x: x.product_id.default_code or ''):
    print('   %-9s %-32s %s' % (l.product_id.default_code,
                                (l.product_id.name or '')[:32], l.product_qty))

# ---------------------------------------------------------------------------
# SEGUNDA PARTE, que hizo falta: cambiar el product_id del move dejo la linea
# con el lote de la bolsa VIEJA (BOL01072501 es de MPBOL01). Hubo que borrarla
# y reasignar. Y _action_assign() no hacia nada porque el move tenia
# picked=True: ignora los movimientos marcados como surtidos. Se baja la
# marca, se reserva y se vuelve a subir, sin tocar amunet_qty_supplied.
#
#   m.move_line_ids.sudo().unlink()
#   m.sudo().picked = False
#   m.sudo()._action_assign()
#   m.sudo().picked = True
#
# Resultado: 940 del lote BOL03102501, y ningun lote cruzado con otro producto.
