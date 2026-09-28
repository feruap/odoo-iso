# Configura el prefijo de lote de tres productos que lo tenian VACIO y por eso
# proponian un numero generico de Odoo (0000001) en vez del lote Amunet.
# Lo reporto Karla el 28-sep-2026: en AMP/IN/00478, MPAGE04 salio como 0000001
# y pidio configurarlo ANTES de validar, para no tener que renombrar despues.
#
# Los tres van en esa MISMA orden. MPDNT01 y MPANT70 ya traen un lote correcto
# escrito (DNT01092601, ANT70092601), pero el numerador les proponia 0000002:
# si se recibe otro lote de ellos, vuelve a salir chatarra. Se corrigen los tres.
#
# NO se toca `tracking`. MPAGE04 esta en 'none' mientras sus hermanos MPAGE01 y
# MPAGE02 estan en 'lot', asi que puede haber ahi otra inconsistencia -pero eso
# cambia si el producto exige lote al recibirse, y es decision de Almacen/Calidad,
# no nuestra. Se comprobo que el prefijo SOLO ya resuelve el nombre.
#
# El prefijo se escribe con el campo amunet_lot_prefix a proposito: su inverse
# CREA la secuencia cuando no existe, que es justo el caso aqui. (En los 19 de
# hoy la secuencia ya existia y se reescribio en su lugar, para no dejar la
# vieja huerfana.)
CASOS = {'MPAGE04': 'AGE04', 'MPDNT01': 'DNT01', 'MPANT70': 'ANT70'}

T = env['product.template'].sudo()
print('%-10s %-12s %-16s %s' % ('CLAVE', 'PREFIJO', 'PROPONE AHORA', 'SECUENCIA'))
for cod, pref in CASOS.items():
    t = T.search([('default_code', '=', cod)], limit=1)
    assert t, 'no existe %s' % cod
    esperado = cod[2:]
    assert pref == esperado, '%s: el prefijo %s no coincide con la clave sin 2 letras (%s)' % (cod, pref, esperado)
    if (t.amunet_lot_prefix or '').strip() == pref:
        print('%-10s %-12s %-16s ya estaba bien' % (cod, pref, '-')); continue
    t.write({'amunet_lot_prefix': pref})
    t.invalidate_recordset()
    pv = t.product_variant_ids[0]
    pv.invalidate_recordset()
    print('%-10s %-12s %-16s %s' % (cod, t.amunet_lot_prefix or '?',
          pv._amunet_next_lot_names(1)[0],
          t.lot_sequence_id.prefix if t.lot_sequence_id else '-'))

env.cr.commit()
print()
print('=== la orden que esperaba Karla ===')
p = env['stock.picking'].sudo().search([('name', '=', 'AMP/IN/00478')], limit=1)
print('  %s  estado=%s' % (p.name, p.state))
for m in p.move_ids:
    pv = m.product_id
    try:
        prop = pv._amunet_next_lot_names(1)[0]
    except Exception:
        prop = '-'
    print('  %-10s lote actual en la linea: %-16s el sistema propondria: %s' % (
        pv.default_code,
        ', '.join(m.move_line_ids.mapped('lot_id.name')) or '-', prop))


# ---------------------------------------------------------------------------
# SEGUNDA PARTE: el lote que ya nacio mal en la orden pendiente.
#
# AMP/IN/00478 tiene la linea de MPAGE04 apuntando al lote "0000001", creado por
# OdooBot el 24-sep con la secuencia generica de Odoo. Karla pidio que el nombre
# quedara bien ANTES de validar, para no renombrar despues.
#
# Se RENOMBRA el lote en vez de crear otro: conserva su lote de fabrica
# (Y202506001) y su caducidad (2028-06-10), que son los datos que importan para
# la trazabilidad. Crear uno nuevo obligaria a recapturarlos.
#
# Se comprobo antes: 0 existencia, 0 movimientos hechos, 0 analisis de calidad,
# una sola linea pendiente (la de esta orden), y el nombre destino esta libre.
LOTE_VIEJO, LOTE_NUEVO = '0000001', 'AGE04092601'

t = env['product.template'].sudo().search([('default_code', '=', 'MPAGE04')], limit=1)
Lot = env['stock.lot'].sudo()
l = Lot.search([('name', '=', LOTE_VIEJO),
                ('product_id', 'in', t.product_variant_ids.ids)], limit=1)
if not l:
    print('\nno hay lote %s en MPAGE04; nada que renombrar' % LOTE_VIEJO)
else:
    # Guardas: no renombrar nada que tenga historia o que choque.
    hechos = env['stock.move.line'].sudo().search_count(
        [('lot_id', '=', l.id), ('state', '=', 'done')])
    assert hechos == 0, 'el lote ya tiene %s movimientos hechos: no se renombra' % hechos
    assert not env['amunet.quality.check'].sudo().search_count([('lot_id', '=', l.id)]), \
        'el lote ya tiene analisis de calidad: no se renombra'
    assert not Lot.search_count([('name', '=', LOTE_NUEVO),
                                 ('product_id', 'in', t.product_variant_ids.ids)]), \
        'el nombre %s ya existe en este producto' % LOTE_NUEVO
    print('\n=== renombrando el lote de MPAGE04 ===')
    print('  antes : %s   (fabrica %s, caducidad %s)' % (
        l.name, getattr(l, 'factory_lot_id', None) and l.factory_lot_id.name or '-',
        l.expiration_date or '-'))
    l.write({'name': LOTE_NUEVO})
    env.cr.commit()
    l.invalidate_recordset()
    print('  ahora : %s   (fabrica %s, caducidad %s)' % (
        l.name, getattr(l, 'factory_lot_id', None) and l.factory_lot_id.name or '-',
        l.expiration_date or '-'))

p = env['stock.picking'].sudo().search([('name', '=', 'AMP/IN/00478')], limit=1)
print()
print('=== AMP/IN/00478 lista para validar ===')
print('  estado: %s' % p.state)
for ml in p.move_line_ids:
    print('  %-10s lote=%s' % (ml.product_id.default_code, ml.lot_id.name if ml.lot_id else '-'))


# ---------------------------------------------------------------------------
# EQGOG01 (Goggles de seguridad UVEX): el mismo hueco. El producto lo dio de
# alta Mery el 28-sep a las 12:04 con la ficha correcta, pero sin prefijo de
# lote, asi que su primer lote habria salido 0000001. Se configura GOG01.
t = env['product.template'].sudo().search([('default_code', '=', 'EQGOG01')], limit=1)
if t and not (t.amunet_lot_prefix or '').strip():
    t.write({'amunet_lot_prefix': 'GOG01'})
    env.cr.commit()
    t.invalidate_recordset()
    pv = t.product_variant_ids[0]
    pv.invalidate_recordset()
    print('\nEQGOG01 -> prefijo %s, propone %s' % (t.amunet_lot_prefix, pv._amunet_next_lot_names(1)[0]))
