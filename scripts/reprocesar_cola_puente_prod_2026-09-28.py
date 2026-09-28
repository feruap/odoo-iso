# Reprocesa la cola del puente de la tienda con el codigo nuevo, para que los
# renglones dejen de decir "fallo tecnico" y digan el motivo real.
#
# No fuerza ningun descuento: solo vuelve a intentar cada movimiento. Lo que
# este bloqueado por el candado de Calidad seguira bloqueado -- que es lo
# correcto-- pero ahora quedara escrito por que.
from odoo import fields
from collections import Counter

C = env['amunet.woo.stock.consumo'].sudo()
err = C.search([('estado', '=', 'error_tecnico')], order='id')
print('renglones en error_tecnico: %s (%s piezas)'
      % (len(err), sum(err.mapped('cantidad'))))
if not err:
    print('nada que reprocesar'); raise SystemExit

backend = err[0].backend_id
for fila in err:
    backend._intentar_movimiento({
        'id': fila.tienda_mov_id, 'product_id': fila.woo_product_id,
        'lote': fila.lote_texto, 'cantidad': fila.cantidad,
        'order_id': fila.pedido_tienda,
        'fecha': fields.Datetime.to_string(fila.fecha_tienda) if fila.fecha_tienda else None,
        'tipo': fila.tipo_tienda or '',
    }, fila)
env.cr.commit()

C.invalidate_model()
print()
print('=== la cola ahora ===')
for k, v in Counter(C.search([]).mapped('estado')).most_common():
    print('  %-18s %s' % (k, v))
print()
print('=== los que estaban en "fallo tecnico" ===')
for r in C.search([('estado', '=', 'lote_retenido')], order='id', limit=3):
    print('  pedido %-8s %-10s lote %-14s' % (
        r.pedido_tienda, r.product_id.default_code or '(SIN MAPEO)',
        r.lot_id.name if r.lot_id else '-'))
    print('     %s' % (r.nota or '')[:150])
