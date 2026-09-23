# La orden viva de CALPROTECTINA quedo como 0926/02/CAL solo porque fue la
# segunda en crearse; la primera (0926/01/CAL, 100 pz) se CANCELO el mismo dia
# sin producir nada ni generar lote. El consecutivo del mes debe ser el 01.
#
# Se aparta la cancelada con el sufijo -CANCELADA y la viva toma el 01. Es la
# misma convencion que ya existe en el sistema: 0926/01/ICN-CANCELADA y
# 0926/01/KEG-CANCELADA, ambas del 3-sep.
#
# Importa porque el nombre de la orden es el numero de LOTE del producto
# terminado: si se queda en /02/, el lote nace con un consecutivo que no
# corresponde y eso va impreso en la etiqueta.
MO = env['mrp.production']
VIVA, CANCELADA = '0926/02/CAL', '0926/01/CAL'

viva = MO.search([('name', '=', VIVA)], limit=1)
assert viva, 'No existe %s' % VIVA
assert viva.state not in ('done', 'cancel'), 'La orden %s no esta viva' % VIVA
assert not viva.lot_producing_ids, 'La orden %s ya tiene lote, no se renombra' % VIVA

vieja = MO.search([('name', '=', CANCELADA)], limit=1)
if vieja:
    assert vieja.state == 'cancel', 'La orden %s NO esta cancelada (%s)' % (CANCELADA, vieja.state)
    assert not vieja.lot_producing_ids, 'La cancelada tiene lote, no se toca'
    vieja.name = '%s-CANCELADA' % CANCELADA
    print('apartada  %s -> %s-CANCELADA (estaba cancelada, sin lote)' % (CANCELADA, CANCELADA))

viva.name = CANCELADA
viva.message_post(body=(
    'Orden renumerada de <b>%s</b> a <b>%s</b>: la anterior 01 se cancelo el '
    'mismo dia sin producir ni generar lote, asi que el consecutivo del mes '
    'corresponde a esta. Pedido por Mery, 23-sep-2026.'
) % (VIVA, CANCELADA))
env.cr.commit()

print('renumerada %s -> %s' % (VIVA, CANCELADA))
print('\n--- ordenes de CALPROTECTINA ---')
for mo in MO.search([('product_id.default_code', '=', 'DMCAL01')], order='id'):
    print('  %-24s %-8s %s pz' % (mo.name, mo.state, mo.product_qty))
