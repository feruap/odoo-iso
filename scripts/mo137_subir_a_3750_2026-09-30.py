"""0926/01/CCF (COVFLU-NET): sube de 3,600 a 3,750 piezas y ajusta lo que hay que surtir.

Pedido por Mery el 30-sep-2026: "suma a que se produzcan 3750 piezas, y por ende surtir
mas material". Confirmado con ella: 3,750 es el TOTAL, o sea +150 sobre las 3,600.

SIN LAS HOJAS MAESTRAS, por indicacion expresa de Mery. La receta pide SPHMC01 y SPHMC15 a
0.4 cm por pieza y esta orden no las trae como componente -- la orden de octubre del mismo
producto si-. Se le pregunto y dijo que no se las pongamos, asi que el consumo de hoja de
esta orden no se registra aqui. No se toca nada de eso.

QUE CAMBIA:
    product_qty        3,600  ->  3,750
    los 5 componentes 1:1 (MPCAC07, STBTR02, STHIS01, STDSC01, MPBOL01)
                       3,600  ->  3,750   (+150 cada uno)
    MICAJ01 (1 caja por 10 piezas, viene del plan de empaque, no de la receta)
                         360  ->    375   (+15)

El material alcanza: 24,795 cartuchos, 14,420 viales, 90,927 hisopos, 128,763 desecantes,
12,936 bolsas y 3,167 cajas en existencia.

LO QUE QUEDA PENDIENTE DE SURTIR, para que Almacen lo sepa:
    +150 de cada componente 1:1, +15 cajas, y los 65 viales que ya faltaban de antes
    (STBTR02 tenia 3,535 surtidos de 3,600 pedidos).

La orden esta EN PROGRESO y con 0 producido, asi que subir la cantidad no contradice nada
ya fabricado. Los moves se ajustan por ORM y no por SQL: asi Odoo recalcula la reserva y
el estado de disponibilidad de cada componente.

Idempotente.
"""
MO = env['mrp.production'].sudo()
NUEVA = 3750.0

mo = MO.browse(137)
assert mo.exists() and mo.name == '0926/01/CCF', 'el id 137 no es 0926/01/CCF'
assert mo.qty_produced == 0, 'la orden ya tiene produccion: %s' % mo.qty_produced

print('=== %s  %s ===' % (mo.name, mo.product_id.default_code))
print('   estado %s   cantidad antes: %s   producido: %s' % (mo.state, mo.product_qty, mo.qty_produced))

if abs(mo.product_qty - NUEVA) < 0.001:
    print('   [ya] la orden ya pide %s' % NUEVA)
else:
    factor = NUEVA / mo.product_qty
    print('   factor de aumento: %.6f' % factor)
    antes = {m.id: m.product_uom_qty for m in mo.move_raw_ids if m.state != 'cancel'}
    mo.write({'product_qty': NUEVA})
    print('   [ok] la orden pide %s' % mo.product_qty)
    print()
    print('   los componentes:')
    for m in mo.move_raw_ids:
        if m.state == 'cancel':
            continue
        viejo = antes.get(m.id, 0.0)
        esperado = viejo * factor
        if abs(m.product_uom_qty - esperado) > 0.01:
            # Odoo no siempre reescala los moves de una MO en progreso: se ajusta a mano
            m.write({'product_uom_qty': esperado})
            print('      %-12s %8.1f -> %8.1f  (ajustado)' % (m.product_id.default_code or '?', viejo, m.product_uom_qty))
        else:
            print('      %-12s %8.1f -> %8.1f' % (m.product_id.default_code or '?', viejo, m.product_uom_qty))
    mo.move_raw_ids._action_assign()

print('\n=== como queda, y que falta surtir ===')
mo.invalidate_recordset()
print('   la orden pide %s %s' % (mo.product_qty, mo.product_uom_id.name))
total_falta = []
for m in mo.move_raw_ids:
    if m.state == 'cancel':
        continue
    sup = m.amunet_qty_supplied or 0.0
    falta = max(0.0, m.product_uom_qty - sup)
    ex = sum(env['stock.quant'].sudo().search(
        [('product_id', '=', m.product_id.id), ('location_id.usage', '=', 'internal')]).mapped('quantity'))
    print('   %-12s pide %8.1f  surtido %8.1f  FALTA SURTIR %7.1f  existencia %9.0f  %s' % (
        m.product_id.default_code or '?', m.product_uom_qty, sup, falta, ex,
        'ok' if ex >= falta else 'NO ALCANZA'))
    if falta > 0:
        total_falta.append((m.product_id.default_code, falta))
print()
print('   resumen de lo que Almacen tiene que surtir:')
for cl, f in total_falta:
    print('      %-12s %8.1f' % (cl, f))
env.cr.commit()
