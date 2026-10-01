# -*- coding: utf-8 -*-
"""AMP/IN/00489: los lotes de las aguas deben ser de OCTUBRE y consecutivo 01.

LO QUE MERY REPORTO: la recepcion trae los lotes ...092602 -- consecutivo 02 de
septiembre- cuando el material llega hoy, 1 de octubre, y no ha llegado ningun otro
lote de esas aguas. Deberian ser ...102601.

DOS CAUSAS DISTINTAS, y conviene separarlas:

1. EL CONSECUTIVO 02. El 01 lo consumieron tres lotes creados el 29-sep a las 23:51
   por la recepcion AMP/IN/00485, de ESTA MISMA solicitud (SC/2026/00006), que despues
   se CANCELO. Al cancelarla, sus lotes se quedaron: ADE01092601, ABI01092601 y
   ATR01092601, los tres con cero movimientos, cero existencia y cero analisis. Nunca
   tuvieron material, pero el consecutivo ya estaba gastado.

   (Esos tres lotes los creo la sesion de desarrollo, o sea nosotros.)

2. EL MES 09. El nombre del lote se fija cuando el lote SE CREA, no cuando el material
   llega. Estos se crearon el 30-sep por la tarde, asi que quedaron con septiembre
   congelado en el nombre aunque la recepcion sea de hoy.

QUE HACE ESTE SCRIPT

   ADE01092602 -> ADE01102601
   ABI01092602 -> ABI01102601
   ATR01092602 -> ATR01102601

Y AVANZA LA SECUENCIA de los tres productos, que es el paso que se olvida: las
secuencias estan en number_next=1, asi que el PROXIMO lote de octubre tambien saldria
...102601 y choca con el que acabamos de poner (stock.lot tiene unico por nombre +
producto). Se deja en 2 para que el siguiente sea ...102602.

NO SE BORRA NADA. Los tres lotes huerfanos de septiembre se quedan donde estan: ya no
estorban, porque al cambiar el mes no hay colision. stock.lot no tiene campo de
archivado, asi que la unica forma de quitarlos seria borrarlos, y eso no se hace sin
pedirlo.

Idempotente: si ya estan renombrados, no hace nada.
"""

CAMBIOS = [
    ('MPADE01', 'ADE01092602', 'ADE01102601'),
    ('MPABI01', 'ABI01092602', 'ABI01102601'),
    ('MPATR01', 'ATR01092602', 'ATR01102601'),
]

pick = env['stock.picking'].search([('name', '=', 'AMP/IN/00489')], limit=1)
print('recepcion %s   state=%s   programada=%s' % (
    pick.name, pick.state, pick.scheduled_date))
from datetime import date as _d
print('hoy: %s\n' % _d.today())

for clave, viejo, nuevo in CAMBIOS:
    tmpl = env['product.template'].search([('default_code', '=', clave)], limit=1)
    lote = env['stock.lot'].search([('name', '=', viejo),
                                    ('product_id.product_tmpl_id', '=', tmpl.id)], limit=1)
    if not lote:
        ya = env['stock.lot'].search([('name', '=', nuevo),
                                      ('product_id.product_tmpl_id', '=', tmpl.id)], limit=1)
        print('  %-9s %s -> %s   %s' % (clave, viejo, nuevo,
                                        'ya estaba renombrado' if ya else '[!] no se encontro'))
        continue
    choca = env['stock.lot'].search([('name', '=', nuevo),
                                     ('product_id.product_tmpl_id', '=', tmpl.id)], limit=1)
    if choca:
        print('  %-9s [!] %s ya existe: NO se toca' % (clave, nuevo))
        continue
    lote.name = nuevo
    print('  %-9s %s -> %s   (renombrado)' % (clave, viejo, nuevo))

    # el paso que se olvida: dejar la secuencia lista para el siguiente
    seq = tmpl.lot_sequence_id
    if seq and seq.number_next_actual <= 1:
        seq.sudo().number_next_actual = 2
        print('              secuencia de %s: number_next 1 -> 2 (el siguiente sera ...102602)' % clave)

env.cr.commit()

print('\n=== COMO QUEDO LA RECEPCION ===')
pick.invalidate_recordset()
for ml in pick.move_line_ids.sorted('id'):
    print('  %-9s %8s  lote=%s' % (
        ml.product_id.default_code, ml.quantity, ml.lot_id.name or ml.lot_name or '(sin lote)'))

print('\n=== los lotes de esas aguas ===')
for clave, _v, _n in CAMBIOS:
    tmpl = env['product.template'].search([('default_code', '=', clave)], limit=1)
    lotes = env['stock.lot'].search([('product_id.product_tmpl_id', '=', tmpl.id)],
                                    order='name')
    seq = tmpl.lot_sequence_id
    print('  %-9s secuencia=%s  proximo numero=%s' % (
        clave, seq.prefix if seq else '-', seq.number_next_actual if seq else '-'))
    for l in lotes[-4:]:
        movs = env['stock.move.line'].search_count([('lot_id', '=', l.id)])
        print('       %-14s creado %s   movimientos=%s%s' % (
            l.name, str(l.create_date)[:10], movs, '   <- huerfano' if not movs else ''))
