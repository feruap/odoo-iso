# AMP/IN/00198 (SPHMC35 lote HMC35072601): la caducidad venia con puntos
# (01.05.2028) y _parse_date no la entiende, por eso no llego a la linea.
# Fijamos la caducidad real 2028-05-01 directo en la linea para desbloquear.
# Autorizado por Fernando 2026-07-20.
ln = env['stock.move.line'].browse(6171)
assert ln.exists() and ln.lot_name == 'HMC35072601', 'linea inesperada'
ln.write({'expiration_date': '2028-05-01 09:00:00'})
print('Linea', ln.id, 'exp:', ln.expiration_date, '| removal:', ln.removal_date,
      '| factory_lot:', ln.factory_lot_id.name)
env.cr.commit()
