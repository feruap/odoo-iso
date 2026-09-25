"""Combos fantasma a cero: ya son hojas en Existencias.

Confirmado por Karla (Almacen MP) el 22-sep-2026: el material de estos combos
ya entro como hojas, asi que el combo que queda en Control de calidad esta
contado dos veces. Causa: el bug de conversion anterior al 28-ago, que daba de
alta las hojas pero movia el combo de lugar en vez de consumirlo.

NO se tocan los dos de antidoping: D000-4055 lo reporto Karla como material
real sin abrir, y D000-8053-A queda fuera hasta analizar su combo de compra.
"""
A_CERO = {'I032-4025': 5.0, 'I163-4045': 50.0}
MOTIVO = ('Combo ya convertido en hojas: contado dos veces. El bug de '
          'conversion anterior al 28-ago-2026 daba de alta las hojas pero '
          'no consumia el combo. Confirmado contra fisico por Karla '
          '(Almacen MP) el 22-sep-2026: las hojas ya estan en Existencias.')

Quant = env['stock.quant']
total = 0
for code, esperado in A_CERO.items():
    prod = env['product.product'].search([('default_code','=',code)], limit=1)
    assert prod, 'no existe %s' % code
    # verificar que sus hojas SI existen antes de dar de baja el combo
    hojas = prod.product_tmpl_id.combo_component_ids.mapped('product_id')
    sin_hoja = []
    for h in hojas:
        cm = sum(Quant.search([('product_id','=',h.id),
                 ('location_id.usage','=','internal')]).mapped('quantity'))
        if cm <= 0:
            sin_hoja.append(h.default_code)
    if sin_hoja:
        print('  %s: OJO, estas hojas estan en cero: %s -- NO se ajusta' % (code, sin_hoja))
        continue
    quants = Quant.search([('product_id','=',prod.id), ('location_id.usage','=','internal')])
    actual = sum(quants.mapped('quantity'))
    if abs(actual - esperado) > 0.001:
        print('  %s: esperaba %g y hay %g -- NO se ajusta, revisar' % (code, esperado, actual))
        continue
    for q in quants:
        if not q.quantity:
            continue
        print('  %-12s %-32s %g -> 0' % (code, q.location_id.complete_name[:32], q.quantity))
        q.with_context(inventory_mode=True).write({
            'inventory_quantity': 0,
            'inventory_diff_quantity': -q.quantity,
        })
        q.with_context(inventory_mode=True).action_apply_inventory()
        total += q.quantity if False else esperado and 0
    prod.product_tmpl_id.message_post(body=MOTIVO)
    total += actual

print('\npiezas ajustadas a cero: %g' % total)
env.cr.commit()
print('OK: cambios guardados.')
