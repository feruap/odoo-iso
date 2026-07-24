# Corrige prefijos de lote que no coinciden con la clave:
# - SPHMC75/76: su secuencia tenia prefijo "HMC53" (compartia el contador de
#   SPHMC53). Sus lotes existentes ya estan bien (HMC75072601/HMC76072601). Solo
#   se corrige la secuencia -> HMC75/HMC76 para los lotes futuros.
# - MPABI01 (Agua bidestilada): secuencia con prefijo "ABD01" -> debe ser "ABI01"
#   (clave MPABI01 sin "MP"). Se corrige la secuencia; se renombra el lote con
#   stock ABD01072601 -> ABI01072601; se archiva el ABD01032601 vacio (colisiona
#   con el ABI01032601 existente).
# Reportado y autorizado por Fernando 2026-07-22.
Tmpl = env['product.template'].sudo()
Lot = env['stock.lot'].sudo()
Prod = env['product.product'].sudo()

# 1) SPHMC75 / SPHMC76 -> prefijo = clave sin 2 letras (HMC75 / HMC76)
for code in ['SPHMC75', 'SPHMC76']:
    t = Tmpl.search([('default_code', '=', code)], limit=1)
    if t:
        t.amunet_lot_prefix = code[2:]
        print(code, '-> prefijo', t.lot_sequence_id.prefix)

# 2) MPABI01 -> prefijo ABI01
t = Tmpl.search([('default_code', '=', 'MPABI01')], limit=1)
t.amunet_lot_prefix = 'ABI01'
print('MPABI01 -> prefijo', t.lot_sequence_id.prefix)
pp = Prod.search([('product_tmpl_id', '=', t.id)], limit=1)

# renombrar el lote con stock ABD01072601 -> ABI01072601 (sin colision)
l = Lot.search([('name', '=', 'ABD01072601'), ('product_id', '=', pp.id)], limit=1)
if l:
    if Lot.search([('name', '=', 'ABI01072601'), ('product_id', '=', pp.id)], limit=1):
        print('OJO: ABI01072601 ya existe, no renombro ABD01072601')
    else:
        l.write({'name': 'ABI01072601'})
        print('renombrado ABD01072601 -> ABI01072601')

# El ABD01032601 vacio (0 stock) colisiona con ABI01032601 existente -> NO se
# renombra ni archiva (stock.lot no es archivable aqui); se deja como leftover
# inofensivo (se puede limpiar despues junto con los fantasma).

env.cr.commit()

# Verificacion: proximo lote de cada uno
for code in ['SPHMC75', 'SPHMC76', 'MPABI01']:
    p = Prod.search([('default_code', '=', code)], limit=1)
    print('  %s -> proximo lote: %s' % (code, p._amunet_next_lot_names(1)))
print('LISTO')
