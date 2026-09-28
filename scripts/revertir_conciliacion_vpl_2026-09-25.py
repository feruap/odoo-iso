# Se devuelve la conciliacion de 0926/01/VPL (MO 152) a 'pendiente' para que
# Produccion la vuelva a hacer. Lo pidio Mery el 25-sep-2026.
#
# QUE ESTABA MAL: la orden declaro 140 piezas de un plan de 216, pero la
# conciliacion se valido con USADO = SURTIDO en los nueve componentes, o sea
# material para las 216. Se inicio y se valido con 45 segundos de diferencia,
# sin tocar ningun numero: quedaron los valores que el sistema precarga como
# punto de partida. Resultado: "Sin sobrante" cuando si hay sobrante.
#
# SE PUEDE REVERTIR SIN MOVER INVENTARIO: amunet_consumo_al_conciliar = True,
# asi que el material sale hasta que ALMACEN firma (estado 'completed'). Esta
# orden quedo en 'validated', y los nueve movimientos siguen en 'assigned':
# ninguno en 'done'. Nada ha salido del almacen.
#
# Lo unico que dejo el paso de validar fue quantity = qty_used y picked = True
# en los movimientos de insumo. Se regresan a picked = False -- si se cerrara la
# orden asi, el nativo los consumiria con la cantidad equivocada -- y se limpia
# amunet_qty_used para que al reiniciar la conciliacion el sistema vuelva a
# precargar desde lo surtido.
MO_ID = 152

mo = env['mrp.production'].browse(MO_ID)
assert mo.exists(), 'no existe la MO %s' % MO_ID
assert mo.reconciliation_state == 'validated', \
    'la conciliacion esta en %s, no en validated' % mo.reconciliation_state

moves = mo.move_raw_ids.filtered(
    lambda m: m.state != 'cancel' and (m.amunet_qty_supplied or 0) > 0)
hechos = moves.filtered(lambda m: m.state == 'done')
assert not hechos, 'hay insumos ya consumidos (%s): no se revierte sin revisar' % \
    ', '.join(hechos.mapped('product_id.default_code'))

print('=== %s  antes ===' % mo.name)
print('conciliacion : %s' % mo.reconciliation_state)
print('validada por : %s el %s' % (mo.reconciliation_validated_by.name,
                                   mo.reconciliation_validated_date))
print('declarado    : %s de un plan de %s' % (mo.qty_producing, mo.product_qty))
print()
previo = []
for m in moves.sorted(lambda x: x.product_id.default_code or ''):
    previo.append('%s usado=%s' % (m.product_id.default_code, m.amunet_qty_used))
    print('  %-10s surtido=%-8s usado=%-8s picked=%s'
          % (m.product_id.default_code, m.amunet_qty_supplied, m.amunet_qty_used, m.picked))

# --- revertir ---------------------------------------------------------------
for m in moves:
    m.sudo().write({'amunet_qty_used': 0.0, 'picked': False})
    abiertas = m.move_line_ids.filtered(lambda l: l.state not in ('done', 'cancel'))
    if abiertas:
        abiertas.sudo().write({'picked': False})

mo.sudo().write({
    'reconciliation_state': 'pending',
    'reconciliation_initiated_by': False,
    'reconciliation_initiated_date': False,
    'reconciliation_validated_by': False,
    'reconciliation_validated_date': False,
})

# La traza queda en el chatter: es un registro ISO 13485 y tiene que decir que
# se revirtio, quien lo pidio y con que valores estaba.
mo.sudo().message_post(body=(
    'La conciliación de materiales se <b>devolvió a Pendiente</b> a petición de '
    'Mery (Desarrollo) para que Producción la vuelva a capturar.<br/><br/>'
    '<b>Por qué:</b> la orden declaró <b>%s</b> pieza(s) de un plan de <b>%s</b>, '
    'pero la conciliación se validó con <b>utilizado = surtido</b> en los nueve '
    'componentes, es decir material para las %s. Se registró "Sin sobrante" '
    'cuando sí hay sobrante que devolver al almacén.<br/><br/>'
    '<b>Estado anterior:</b> Validada por producción (%s, %s).<br/>'
    '<b>Valores que se limpiaron:</b> %s.<br/><br/>'
    'No se movió inventario: el consumo de esta orden ocurre cuando Almacén '
    'firma la conciliación, y eso no había pasado. Los nueve movimientos de '
    'insumo siguen reservados, ninguno consumido.'
) % (mo.qty_producing, mo.product_qty, mo.product_qty,
     'Kimberli Garista De la Cruz', '2026-09-24 20:10',
     '; '.join(previo)))

env.cr.commit()

mo = env['mrp.production'].browse(MO_ID)
print()
print('=== despues ===')
print('conciliacion : %s' % mo.reconciliation_state)
print('iniciada por : %s' % (mo.reconciliation_initiated_by.name or '-'))
print('validada por : %s' % (mo.reconciliation_validated_by.name or '-'))
for m in mo.move_raw_ids.filtered(lambda m: m.state != 'cancel' and (m.amunet_qty_supplied or 0) > 0).sorted(lambda x: x.product_id.default_code or ''):
    print('  %-10s surtido=%-8s usado=%-8s picked=%-6s estado=%s'
          % (m.product_id.default_code, m.amunet_qty_supplied, m.amunet_qty_used,
             m.picked, m.state))
