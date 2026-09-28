# Cancela AMP/QC/00378 y AMP/QC/00380, las liberaciones de cuarentena de dos
# equipos de uso interno. Autorizado por Mery el 28-sep-2026.
#
# POR QUE SOBRAN: un equipo de uso interno NO pasa por la cuarentena de materia
# prima. Su ruta es la Solicitud de Ingreso de Equipo (modulo de Validacion),
# donde se registra marca, modelo, serie, area y funcion, y se decide si
# requiere calibracion o calificacion. Al validar la recepcion se generaron LAS
# DOS vias a la vez, en el mismo minuto y desde la misma recepcion:
#
#   31-jul 16:41  AMP/IN/00268 -> SOL-EQ-0001 (Validacion) + AMP/QC/00378
#   03-ago 19:53  AMP/IN/00272 -> SOL-EQ-0002 y 0003       + AMP/QC/00380
#
# Se cancela la via de cuarentena y se conserva la de Validacion, que es la
# correcta y la que lleva los datos del equipo.
#
# OJO: aqui el material SI esta disponible (3 pz en AMP/Entrada). No se cancela
# por falta de existencia -como las seis fantasma de hoy- sino por ruta
# equivocada, asi que la guarda es OTRA: se exige que exista la solicitud de
# Validacion gemela. Sin ella no se cancela nada.
from odoo import fields

CASOS = {
    'AMP/QC/00378': ('AMP/IN/00268', 'Camara de vacio Vevor Y2, serie 25122076050030124, '
                     'codigo CAL/COM/02-02, para Control de calidad (ensayos de '
                     'hermeticidad).'),
    'AMP/QC/00380': ('AMP/IN/00272', 'Dos tablets HOTWAV R8, series TABR80000000010324 y '
                     'TABR80000000014725.'),
}

P = env['stock.picking'].sudo()
Req = env['amunet.equipment.request'].sudo()
print('%-14s %-10s %-28s %s' % ('DOCUMENTO', 'ANTES', 'SOLICITUD GEMELA', 'RESULTADO'))
for nombre, (recepcion, detalle) in CASOS.items():
    p = P.search([('name', '=', nombre)], limit=1)
    if not p or p.state in ('done', 'cancel'):
        print('%-14s %-10s %-28s sin cambios' % (nombre, p.state if p else '-', '-')); continue
    qc = getattr(p, 'amunet_disposition_qc_id', False)
    assert not qc, '%s tiene analisis ligado (%s): revisar a mano' % (nombre, qc.name if qc else '')
    # La guarda de este caso: tiene que existir la via buena.
    pick_rec = P.search([('name', '=', recepcion)], limit=1)
    gemelas = Req.search([('picking_id', '=', pick_rec.id)]) if pick_rec else Req
    assert gemelas, ('%s: no existe Solicitud de Ingreso de Equipo para la recepcion %s. '
                     'Sin la via buena NO se cancela: el material se quedaria sin ruta.'
                     % (nombre, recepcion))
    antes = p.state
    p.message_post(body=(
        'Documento <b>cancelado</b> por Desarrollo, autorizado por Mery.<br/><br/>'
        '<b>Motivo:</b> un equipo de uso interno no pasa por la cuarentena de '
        'materia prima. Su ruta es la Solicitud de Ingreso de Equipo, donde se '
        'registran marca, modelo, serie, area y funcion, y se decide si requiere '
        'calibracion o calificacion.<br/><br/>Al validar la recepcion %(rec)s se '
        'generaron las dos vias a la vez. Se conserva la de Validacion '
        '(<b>%(sol)s</b>) y se cancela esta.<br/><br/><b>Material:</b> %(det)s<br/><br/>'
        'No mueve inventario: el documento no estaba validado. Las piezas siguen '
        'en AMP/Entrada, a la espera de que se cierre la solicitud de Validacion.'
    ) % {'rec': recepcion, 'sol': ', '.join(gemelas.mapped('name')), 'det': detalle})
    p.action_cancel()
    p.invalidate_recordset()
    print('%-14s %-10s %-28s -> %s' % (nombre, antes, ', '.join(gemelas.mapped('name')), p.state))

env.cr.commit()
print()
print('=== liberaciones que quedan pendientes ===')
for x in P.search([('name', 'like', 'AMP/QC/'), ('state', 'not in', ('done', 'cancel'))], order='name'):
    print('  %-14s %-10s %s' % (x.name, x.state, ', '.join(x.move_ids.mapped('product_id.default_code'))[:40]))
