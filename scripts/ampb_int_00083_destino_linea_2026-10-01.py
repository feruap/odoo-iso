# -*- coding: utf-8 -*-
"""AMPB/INT/00083: corregir el destino de la linea para que se pueda validar.

EL BUG, que es recurrente y conocido desde el 18-ago-2026: el tipo de operacion
"Traslados internos" de Burgos (picking type 23) tiene como destino por defecto
AMPB/Existencias, el MISMO que su origen. Cuando se hace un traslado a Fabrica, el
operador cambia el destino en el ENCABEZADO a AMP/Existencias, pero la LINEA DE
OPERACION conserva el destino por defecto. Queda asi:

    encabezado   AMPB/Existencias -> AMP/Existencias     (bien)
    movimiento   AMPB/Existencias -> AMP/Existencias     (bien)
    LINEA        AMPB/Existencias -> AMPB/Existencias    <- el material no se moveria

El candado que se puso en agosto hizo exactamente su trabajo: bloqueo la validacion
antes de que el traslado quedara "hecho" sin mover nada. Antes de ese candado, cinco
traslados quedaron en falso y el material se quedo en Burgos mientras el sistema decia
que estaba en Fabrica.

Aqui solo se corrige el destino de la linea para que coincida con el movimiento. No se
cambia cantidad, ni lote, ni se valida: eso lo hace el operador.
"""

pick = env['stock.picking'].search([('name', '=', 'AMPB/INT/00083')], limit=1)
assert pick, 'no existe AMPB/INT/00083'
print('%s   state=%s' % (pick.name, pick.state))
print('  encabezado: %s -> %s' % (pick.location_id.complete_name, pick.location_dest_id.complete_name))

arregladas = 0
for ml in pick.move_line_ids:
    mv = ml.move_id
    print('\n  linea %s  %s  lote=%s  cant=%s' % (
        ml.id, ml.product_id.default_code, ml.lot_id.name or '-', ml.quantity))
    print('     movimiento dice: %s -> %s' % (mv.location_id.complete_name, mv.location_dest_id.complete_name))
    print('     la linea dice:   %s -> %s' % (ml.location_id.complete_name, ml.location_dest_id.complete_name))
    if ml.location_id == ml.location_dest_id and mv.location_dest_id != ml.location_dest_id:
        ml.location_dest_id = mv.location_dest_id
        arregladas += 1
        print('     [+] corregida a: %s -> %s' % (
            ml.location_id.complete_name, ml.location_dest_id.complete_name))
    elif ml.location_dest_id != mv.location_dest_id:
        print('     [!] la linea no coincide con el movimiento pero el origen es distinto: revisar a mano')
    else:
        print('     ya estaba bien')

env.cr.commit()
pick.invalidate_recordset()

print('\n=== COMO QUEDO ===')
print('  lineas corregidas: %s' % arregladas)
for ml in pick.move_line_ids:
    print('  %s  %s  %s -> %s   cant=%s  lote=%s' % (
        ml.id, ml.product_id.default_code, ml.location_id.complete_name,
        ml.location_dest_id.complete_name, ml.quantity, ml.lot_id.name or '-'))
en_falso = pick.move_line_ids.filtered(lambda x: x.quantity and x.location_id == x.location_dest_id)
print('\n  lineas en falso que quedan: %s' % len(en_falso))
print('  el traslado %s' % ('YA SE PUEDE VALIDAR' if not en_falso else 'SIGUE BLOQUEADO -- revisar'))
