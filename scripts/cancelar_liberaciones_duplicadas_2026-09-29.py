# -*- coding: utf-8 -*-
"""Cancelar 13 liberaciones de Calidad que quedaron duplicadas.

QUE PASO. Cuando Calidad libera un lote, el material sale de Control de
calidad hacia Existencias. En estos 13 casos el material SI salio, pero por
un documento distinto: quedaron dos papeles para un solo movimiento y solo
uno se cerro. El otro se quedo abierto pidiendo mover algo que ya no esta.

Comprobado uno por uno. Ejemplos:
  AMP/STOR/00079 pide 557 de MPCAR27; AMP/QC/00374 movio esos mismos 557 el
    mismo dia, 22-jul.
  AMP/STOR/00086 pide 60 cm de SPHMC33; AMP/QC/00376 movio los 60 el mismo
    dia, 27-jul.
  AMP/STOR/00102 pide 50 de STCPL10; AMP/IN/00393 movio 47 el 03-sep (los 3
    de diferencia son la muestra que Calidad se quedo).
  Igual STCNL01, STBBM02 y STCPL15.

Hoy los 13 tienen CERO existencia en Control de calidad: no se pueden validar
de ninguna forma. Cancelarlos no mueve inventario -- el material ya esta donde
debe --; lo que se quita es un papel que no corresponde a la realidad y que
ensucia la lista de pendientes de Almacen.

El script se niega a cancelar cualquiera que todavia tenga material en
Control de calidad.
"""
DOCS = ['AMP/STOR/00047', 'AMP/STOR/00048', 'AMP/STOR/00049', 'AMP/STOR/00053',
        'AMP/STOR/00055', 'AMP/STOR/00056', 'AMP/STOR/00079', 'AMP/STOR/00086',
        'AMP/STOR/00102', 'AMP/STOR/00108', 'AMP/STOR/00111', 'AMP/STOR/00117',
        'AMP/STOR/00124']

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

hechos, frenados = [], []
for nombre in DOCS:
    p = env['stock.picking'].search([('name', '=', nombre)], limit=1)
    if not p:
        frenados.append((nombre, 'no existe'))
        continue
    if p.state == 'cancel':
        hechos.append((nombre, 'ya estaba cancelado'))
        continue
    # Candado: si el material sigue en Control de calidad, NO se cancela.
    con_material = []
    for m in p.move_ids:
        en_cc = sum(env['stock.quant'].search([
            ('product_id', '=', m.product_id.id),
            ('location_id.complete_name', 'ilike', 'Control de calidad')]).mapped('quantity'))
        if en_cc > 0:
            con_material.append('%s tiene %s en CC' % (m.product_id.default_code, en_cc))
    if con_material:
        frenados.append((nombre, 'NO se cancela: ' + '; '.join(con_material)))
        continue
    detalle = ', '.join('%s x%s' % (m.product_id.default_code, m.product_uom_qty)
                        for m in p.move_ids)
    p.action_cancel()
    p.message_post(body=(
        'Cancelado por duplicado: el material ya habia salido de Control de '
        'calidad por otro documento. Hoy queda cero en cuarentena, asi que este '
        'traslado no se podia cerrar. Revisado con Mery el 29-sep-2026.'))
    p.invalidate_recordset()
    (hechos if p.state == 'cancel' else frenados).append((nombre, '%s | %s' % (p.state, detalle)))

env.cr.commit()

print('=' * 78)
print('CANCELADOS: %d' % len(hechos))
for n, d in hechos:
    print('  %-16s %s' % (n, d))
print('FRENADOS: %d' % len(frenados))
for n, d in frenados:
    print('  %-16s %s' % (n, d))
print('=' * 78)
