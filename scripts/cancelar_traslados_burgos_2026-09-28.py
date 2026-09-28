# Cancela los traslados pendientes de Burgos que Karla pidio cancelar el
# 28-sep-2026: "Revise los traslados pendientes y mi respuesta es cancelar
# todos... Cuando se cancelen, si Fabrica realmente necesita el material lo
# pedimos de nuevo de forma manual."
#
# SU RAZON, grupo por grupo:
#   A. MPBOL05, 6 traslados, 612 pz -> los genero la regla automatica, nadie los
#      pidio a mano.
#   B. MIFUN07, 4 traslados, 81 pz  -> igual, automaticos.
#   C. agua destilada, tridestilada y crioviales -> Burgos no tiene existencia.
#      COMPROBADO: MPADE01=0, MPATR01=0, COCRI02=0 en AMPB.
#   D. 7 borradores desde mayo, incluidos los 2 con material (COTUB02, STTCT02).
#
# OJO - se quedan FUERA dos que ella no menciono, y a proposito:
#   AMP/INT/00003 (STTCT02) y AMP/INT/00010 (STHIS01), los dos con demanda 0 y
#   van de AMP hacia Burgos, no al contrario. No estaban en su lista y no se
#   tocan sin preguntarle.
#
# No se mueve inventario: ninguno esta validado. Cancelar libera las reservas,
# que es justo lo que estaba trabando el material en Burgos.
DOCS = ['AMPB/OUT/%05d' % i for i in range(4, 17)] + \
       ['AMPB/INT/%05d' % i for i in range(22, 29)]

P = env['stock.picking'].sudo()
locs = env['stock.location'].sudo().search([('complete_name', 'ilike', 'AMPB')])
print('%-16s %-10s %-26s %s' % ('DOCUMENTO', 'ANTES', 'PRODUCTO(S)', 'RESULTADO'))
n = 0
for nombre in DOCS:
    p = P.search([('name', '=', nombre)], limit=1)
    if not p:
        print('%-16s %-10s %-26s no existe' % (nombre, '-', '-')); continue
    if p.state in ('done', 'cancel'):
        print('%-16s %-10s %-26s ya estaba, no se toca' % (nombre, p.state, '-')); continue
    # Guarda: solo traslados que toquen Burgos. Si alguno no, se detiene.
    assert (p.location_id in locs) or (p.location_dest_id in locs), \
        '%s no toca ninguna ubicacion de Burgos: revisar a mano' % nombre
    prods = ', '.join('%s(%s)' % (m.product_id.default_code, m.product_uom_qty)
                      for m in p.move_ids)[:26] or '(sin lineas)'
    antes = p.state
    p.message_post(body=(
        'Traslado <b>cancelado</b> por Desarrollo, a peticion de Karla '
        '(Almacen MP) del 28-sep-2026.<br/><br/><b>Motivo:</b> los generó la '
        'regla de reabastecimiento automatico, nadie los pidio a mano, y en '
        'varios casos Burgos no tiene existencia del material. Si Fabrica '
        'realmente lo necesita, se pide de nuevo de forma manual.<br/><br/>'
        'No mueve inventario: el traslado no estaba validado. Cancelar libera '
        'la reserva que tenia tomada.'))
    p.action_cancel()
    p.invalidate_recordset()
    print('%-16s %-10s %-26s -> %s' % (nombre, antes, prods, p.state))
    n += 1

env.cr.commit()
print()
print('canceladas: %s' % n)
print()
print('=== traslados de Burgos que quedan pendientes ===')
for p in P.search([('state', 'not in', ('done', 'cancel')), '|',
                   ('location_id', 'in', locs.ids), ('location_dest_id', 'in', locs.ids)], order='name'):
    print('  %-16s %-10s %-24s -> %-24s %s' % (p.name, p.state,
          p.location_id.complete_name[:24], p.location_dest_id.complete_name[:24],
          ', '.join(p.move_ids.mapped('product_id.default_code'))))
