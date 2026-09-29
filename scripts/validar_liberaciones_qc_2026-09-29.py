# -*- coding: utf-8 -*-
"""Cerrar las 7 liberaciones de Calidad que si se pueden cerrar.

De los 24 movimientos Control de calidad -> Existencias que llevaban semanas
abiertos, estos 7 estan completos: lote reservado y material presente en
Control de calidad. Lo unico que les faltaba era que alguien los validara.
Los tres ultimos son de ayer.

Los otros 17 NO se tocan aqui: 13 piden mover material que ya no esta en
Control de calidad, y 4 tienen conflicto de cantidades. Esos se ven aparte.

Se valida por la ORM, con button_validate, que es lo que corre el operador:
asi pasan los candados del flujo en vez de saltarselos.

Idempotente: lo ya validado se omite.
"""
DOCS = ['AMP/STOR/00114', 'AMP/STOR/00116', 'AMP/STOR/00125',
        'AMP/STOR/00135', 'AMP/STOR/00141', 'AMP/STOR/00142', 'AMP/STOR/00143']

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

hechos, fallados = [], []
for nombre in DOCS:
    p = env['stock.picking'].search([('name', '=', nombre)], limit=1)
    if not p:
        fallados.append((nombre, 'no existe'))
        continue
    if p.state == 'done':
        hechos.append((nombre, 'ya estaba validado'))
        continue
    detalle = ', '.join('%s x%s' % (m.product_id.default_code, m.product_uom_qty)
                        for m in p.move_ids)
    try:
        # El flujo de tres pasos pide aprobar antes de validar.
        if not p.transfer_approved:
            p.action_transfer_approve()
        res = p.button_validate()
        if isinstance(res, dict) and res.get('res_model'):
            # Odoo pide confirmar algo (backorder, cantidad): se responde igual
            # que en pantalla para no dejar el documento a medias.
            wiz = env[res['res_model']].with_context(res.get('context') or {}).create({})
            (wiz.process_cancel_backorder if hasattr(wiz, 'process_cancel_backorder')
             else wiz.process)()
        p.invalidate_recordset()
        (hechos if p.state == 'done' else fallados).append(
            (nombre, '%s -> %s | %s' % ('ok' if p.state == 'done' else p.state, p.state, detalle)))
    except Exception as e:
        fallados.append((nombre, '%s: %s' % (type(e).__name__, str(e)[:110])))

env.cr.commit()

print('=' * 78)
print('VALIDADOS: %d' % len(hechos))
for n, d in hechos:
    print('  %-16s %s' % (n, d))
print('NO SE PUDO: %d' % len(fallados))
for n, d in fallados:
    print('  %-16s %s' % (n, d))
print('=' * 78)
