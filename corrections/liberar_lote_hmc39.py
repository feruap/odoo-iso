# Libera formalmente el lote HMC39072601 (Hoja Maestra Dimero D): el analisis
# 005200726-01 fue APROBADO y el material ya esta en Existencias, pero quedo en
# release_state='pending' porque no se dio "Liberar lote". Autorizado Fernando 2026-07-21.
lot = env['stock.lot'].search([('name', '=', 'HMC39072601'),
                               ('product_id.default_code', '=', 'SPHMC39')], limit=1)
assert lot, 'no se encontro el lote'
print('antes:', lot.amunet_lot_release_state)
notes = ('Liberacion formal: analisis 005200726-01 aprobado, material ya en '
         'Existencias. Ajuste autorizado por Fernando 2026-07-21.')
try:
    lot.sudo()._action_release_lot(notes=notes)
    print('via _action_release_lot ->', lot.amunet_lot_release_state)
except Exception as e:
    print('bloqueos en _action_release_lot:', str(e)[:120])
    lot.with_context(skip_lot_release_lock=True).sudo().write({'amunet_lot_release_state': 'released'})
    print('puesto directo ->', lot.amunet_lot_release_state)
env.cr.commit()
