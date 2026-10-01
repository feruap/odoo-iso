# 0926/01/CCF: mover al piso el material surtido. Produccion firmo que lo
# recibio el 28-sep, pero la orden tenia el flujo apagado y luego no se pudo
# mover porque su buffer viene en DOS lotes (3,535 + 215) y el traslado solo
# sabia manejar uno. Arreglado en amunet_production 19.0.1.66.0 (PR #161).
mo = env['mrp.production'].search([('name', '=', '0926/01/CCF')])
print('antes:')
for m in mo.move_raw_ids.sorted(lambda x: x.product_id.default_code or ''):
    print('   %-9s %-26s surtido %9s' % (
        m.product_id.default_code, m.location_id.complete_name, m.amunet_qty_supplied))
pk = mo.sudo()._amunet_surtido_a_piso()
env.cr.commit()
print()
print('traslado:', pk.name if pk else 'NINGUNO')
if pk:
    for mv in pk.move_ids.sorted(lambda x: x.product_id.default_code or ''):
        for ml in mv.move_line_ids:
            print('   %-9s lote %-14s %9s' % (
                mv.product_id.default_code, ml.lot_id.name or '-', ml.quantity))
print()
print('despues: de donde sale cada componente')
for m in mo.move_raw_ids.sorted(lambda x: x.product_id.default_code or ''):
    print('   %-9s %s' % (m.product_id.default_code, m.location_id.complete_name))
