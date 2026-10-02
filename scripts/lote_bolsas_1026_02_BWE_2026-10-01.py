# -*- coding: utf-8 -*-
"""La orden de bolsas Whirl-Pak: el lote queda 1026/02/BWE.

QUE PASABA. El lote del producto terminado se llamaba "AMP/MO/00039": el folio GENERAL
de la orden, no un lote. El lote toma el nombre de la orden cuando se crea, y este se
creo mientras la orden todavia se llamaba AMP/MO/00039, antes de que el 30-sep se le
configurara su folio propio (/BWE). La orden ya quedo como 0926/01/BWE; el lote se habia
quedado con el nombre viejo.

Mery indico el nombre: 1026/02/BWE. El material se produce en octubre, de ahi el 1026.

SE RENOMBRA, no se crea uno nuevo: el lote ya esta ligado al movimiento del producto
terminado. Crear otro obligaria a reasignar el movimiento y dejaria el viejo colgando.

Comprobado antes: el lote tiene un solo movimiento (el de esta orden, sin validar), cero
existencia y ningun analisis. El nombre 1026/02/BWE esta libre.

OJO CON EL MOMENTO: la orden esta en "por cerrar". Si se cierra antes de esto, el nombre
AMP/MO/00039 queda escrito en el inventario, en la etiqueta y en la trazabilidad del
producto terminado.
"""

VIEJO = 'AMP/MO/00039'
NUEVO = '1026/02/BWE'

mo = env['mrp.production'].browse(180)
print('orden %s   state=%s   %s pz' % (mo.name, mo.state, mo.product_qty))

lote = env['stock.lot'].search([('name', '=', VIEJO),
                                ('product_id.product_tmpl_id.default_code', '=', 'PTBWP01')], limit=1)
if not lote:
    ya = env['stock.lot'].search([('name', '=', NUEVO),
                                  ('product_id.product_tmpl_id.default_code', '=', 'PTBWP01')], limit=1)
    print('  %s' % ('ya estaba renombrado a %s' % NUEVO if ya else '[!] no se encontro el lote %s' % VIEJO))
else:
    choca = env['stock.lot'].search([('name', '=', NUEVO),
                                     ('product_id', '=', lote.product_id.id)], limit=1)
    assert not choca, 'ya existe un lote %s para este producto' % NUEVO
    movs = env['stock.move.line'].search_count([('lot_id', '=', lote.id)])
    quants = env['stock.quant'].search_count([('lot_id', '=', lote.id)])
    print('  lote actual: %s   movimientos=%s  quants=%s' % (lote.name, movs, quants))
    lote.name = NUEVO
    lote.message_post(body=(
        'Lote renombrado de <b>%s</b> a <b>%s</b>. El nombre anterior era el folio general '
        'de la orden, no un lote: se creo antes de que la orden tuviera su folio propio '
        '(/BWE). Indicado por Mery el 01-oct-2026.') % (VIEJO, NUEVO))
    print('  renombrado a: %s' % lote.name)

env.cr.commit()

print('\n=== COMO QUEDO ===')
mo.invalidate_recordset()
print('  orden: %s   state=%s' % (mo.name, mo.state))
for ml in mo.move_finished_ids.move_line_ids:
    print('  producto terminado: %-9s lote=%-14s cantidad=%s  destino=%s' % (
        ml.product_id.default_code, ml.lot_id.name or ml.lot_name or '(sin lote)',
        ml.quantity, ml.location_dest_id.complete_name))
print('\n  lotes de PTBWP01:')
for l in env['stock.lot'].search([('product_id.product_tmpl_id.default_code', '=', 'PTBWP01')], order='name'):
    print('     %-14s creado %s' % (l.name, str(l.create_date)[:10]))
