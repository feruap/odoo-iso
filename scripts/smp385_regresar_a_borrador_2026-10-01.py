# -*- coding: utf-8 -*-
"""SMP/26/00385 (id 400): regresarla a borrador.

Pedido de Mery el 01-oct-2026.

POR QUE SON DOS PASOS Y NO UNO: action_draft() del modulo solo acepta venir del estado
CANCELADA ("Solo desde Cancelada se regresa a Borrador"). La solicitud estaba en
Enviada, asi que el camino es cancelar y despues regresar. No es un rodeo: es el camino
que el modulo define.

SEGURO DE HACER, comprobado antes: la solicitud no tiene transferencia (picking_id
vacio) y sus 6 renglones estan en cero surtido y cero recibido. Cancelar no mueve ni
una pieza de inventario.

QUE SE PIERDE AL REGRESARLA: la firma de quien la solicito (Alondra Sanchez, el
01-oct). Es lo correcto -- al volver a borrador habra que enviarla de nuevo y firmarla
de nuevo-, pero conviene saberlo: si Alondra ya no esta disponible, alguien mas tendra
que firmar el envio.

Los 6 renglones y sus cantidades NO se tocan.
"""

# El odoo shell corre como OdooBot, que no es el solicitante ni material manager, y
# action_cancel se lo niega. Se corre como Mery, que si tiene el rol.
mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
assert mery, 'no existe el usuario de Mery'
env = env(user=mery.id)
print('ejecutando como: %s' % mery.name)

req = env['amunet.material.request'].browse(400)
print('%s   state=%s' % (req.name, req.state))
print('  solicito: %s' % (req.user_requested_id.name or '-'))
print('  transferencia: %s' % (req.picking_id.name if req.picking_id else 'ninguna'))
print('  renglones: %s' % len(req.line_ids))
for l in req.line_ids.sorted('id'):
    print('     %-9s pedido=%-8s surtido=%-6s recibido=%s' % (
        l.product_id.default_code, l.qty_requested, l.qty_supplied, l.qty_received))

assert not req.picking_id, 'tiene transferencia: NO se toca sin revisar'
assert not any(l.qty_supplied or l.qty_received for l in req.line_ids), \
    'hay material surtido o recibido: NO se toca sin revisar'

if req.state == 'draft':
    print('\n  ya estaba en borrador')
else:
    if req.state != 'cancelled':
        req.action_cancel()
        print('\n  paso 1: cancelada')
    req.action_draft()
    print('  paso 2: regresada a borrador')

env.cr.commit()
req.invalidate_recordset()

print('\n=== COMO QUEDO ===')
print('  %s   state=%s' % (req.name, req.state))
print('  firma de solicitud: %s' % (req.user_requested_id.name or '(limpia, hay que volver a enviarla)'))
print('  transferencia:      %s' % (req.picking_id.name if req.picking_id else 'ninguna'))
print('  renglones intactos: %s' % len(req.line_ids))
for l in req.line_ids.sorted('id'):
    print('     %-9s pedido=%-8s state=%s' % (l.product_id.default_code, l.qty_requested, l.state))
