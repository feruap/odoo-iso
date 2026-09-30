"""Marca la exencion de analisis previo al sistema en las ordenes que la RS ya libero.

Autorizado por Mery el 30-sep-2026, a partir del reporte de Almacen de PT del 22-sep
(siete lotes atorados) y del barrido que salio de ahi.

LA SITUACION. Hay ordenes de junio y julio de 2026 en las que:
    - el LOTE esta liberado, firmado por la Responsable Sanitaria el 14-ago-2026, con la
      nota "Liberacion retroactiva: producto analizado antes de existir la infraestructura
      de liberacion en el sistema", y
    - la ORDEN sigue con su analisis en "Pendiente de Solicitar" y sin la exencion marcada.

Son dos candados distintos, y por eso el caso se veia contradictorio: el del lote ya
estaba resuelto por la RS, el de la orden seguia cerrado. Cuando Almacen intentaba sacar
material de esos lotes, el candado de salida lo frenaba con "el analisis de calidad del MO
esta en estado Pendiente de Solicitar", aunque la liberacion existiera.

EL MECANISMO YA ESTABA PREVISTO. El campo amunet_qc_previo_al_sistema existe justo para
esto, y el propio candado lo dice en su comentario: "Exencion explicita, orden por orden:
el analisis existe en papel y es anterior al flujo en Odoo. Se marca a mano y queda en el
historial de la orden. No hay corte por fecha a proposito, para que ninguna orden nueva
quede exenta sola." Ya se usaba en 10 ordenes; esto completa las que faltaban.

EL BLINDAJE, y es lo que hace que esto no sea un bypass: se exenta UNICAMENTE la orden
cuyo lote ya esta liberado POR LA RS y CON NOTA. Si el lote no esta liberado, o esta
liberado sin nota, la orden NO se toca: en ese caso no hay respaldo documental y la
exencion seria un atajo, no un registro.

Ninguno de estos lotes tiene piezas entregadas a cliente, asi que no hay material fuera
esperando este registro.

Idempotente.
"""
from markupsafe import Markup

MO = env['mrp.production'].sudo()

RS_ESPERADA = 'Patricia'   # la Responsable Sanitaria que firmo la liberacion retroactiva

candidatas = MO.search([('quality_analysis_status', '=', 'to_request'),
                        ('state', '=', 'done')])
print('ordenes terminadas con analisis sin solicitar: %d' % len(candidatas))

marcadas = ya = sin_respaldo = 0
print('\n=== revisando una por una ===')
for mo in candidatas:
    if mo.amunet_qc_previo_al_sistema:
        ya += 1
        continue
    lotes_ok, lotes_no = [], []
    for l in mo.lot_producing_ids:
        libre = l.amunet_lot_release_state == 'released'
        nota = (l.amunet_lot_release_notes or '').strip()
        firma = l.amunet_lot_released_by_id.name or ''
        if libre and nota and RS_ESPERADA.lower() in firma.lower():
            lotes_ok.append((l, nota, firma, l.amunet_lot_released_date))
        else:
            lotes_no.append((l, libre, bool(nota), firma))
    if not lotes_ok:
        if mo.lot_producing_ids:
            sin_respaldo += 1
            print('   [no] %-14s %-9s sin respaldo de la RS: %s' % (
                mo.name, mo.product_id.default_code or '?',
                '; '.join('lote %s liberado=%s nota=%s firma="%s"' % (
                    l.name, lb, nt, f[:18]) for l, lb, nt, f in lotes_no)))
        continue
    # hay respaldo: se marca la exencion y se deja el porque en el historial
    l, nota, firma, fecha = lotes_ok[0]
    mo.write({'amunet_qc_previo_al_sistema': True})
    mo.message_post(body=Markup(
        'Marcada la <b>exención de análisis previo al sistema</b> el 30-sep-2026, '
        'autorizado por Mery.<br/><br/>'
        'Esta orden es del %(fab)s y su análisis se hizo <b>en papel</b>, antes de que '
        'el flujo de análisis existiera en Odoo. El respaldo es la liberación del lote '
        '<b>%(lote)s</b>, firmada por <b>%(firma)s</b> (Responsable Sanitaria) el '
        '%(fecha)s con la nota:<br/><i>%(nota)s</i><br/><br/>'
        'Sin esta marca, el candado de salida frenaba cualquier movimiento del material '
        'a cliente con el mensaje de que el análisis estaba "Pendiente de Solicitar", '
        'aunque la Responsable Sanitaria ya lo hubiera liberado. La exención NO sustituye '
        'al análisis: registra que existe fuera del sistema y quién lo autorizó.'
    ) % {'fab': str(mo.date_finished or '')[:10], 'lote': l.name, 'firma': firma,
         'fecha': str(fecha)[:16], 'nota': nota})
    marcadas += 1
    print('   [ok] %-14s %-9s lote %-14s  RS %s  %s' % (
        mo.name, mo.product_id.default_code or '?', l.name, firma[:20], str(fecha)[:10]))

print()
print('   exentadas ahora:        %d' % marcadas)
print('   ya estaban exentas:     %d' % ya)
print('   sin respaldo, sin tocar: %d' % sin_respaldo)

print('\n=== como queda ===')
print('   ordenes con la exencion: %d' % MO.search_count([('amunet_qc_previo_al_sistema','=',True)]))
faltan = 0
for mo in MO.search([('quality_analysis_status','=','to_request'),('state','=','done'),
                     ('amunet_qc_previo_al_sistema','=',False)]):
    if any(l.amunet_lot_release_state == 'released' for l in mo.lot_producing_ids):
        faltan += 1
print('   lote liberado sin exencion todavia: %d' % faltan)
env.cr.commit()
