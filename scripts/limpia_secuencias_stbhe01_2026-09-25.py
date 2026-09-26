# -*- coding: utf-8 -*-
"""Limpiar el enredo de secuencias del buffer de heces (STBHE01).

Karla reporto que el prefijo seguia mal. El prefijo de la secuencia ACTIVA ya se
corrigio (HEB01 -> BHE01), pero al revisar aparecio que el producto arrastra
CUATRO secuencias, tres de ellas huerfanas:

    id=788    prefix=HEB01   huerfana    residuo con el prefijo malo
    id=2000   prefix=BHE01   la activa   code=amunet.lot.HEB01.1000
    id=2583   prefix=BHE01   huerfana    code=amunet.lot.BHE01.prod
    id=2584   prefix=BHE01   huerfana    code=amunet.lot.BHE01.2321

Las dos huerfanas con BHE01 dicen que alguien ya intento arreglarlo antes y
quedo a medias. Y la activa tiene el prefijo bien pero su CODE todavia dice
HEB01: funciona -- lo unico que se valida es que empiece con 'amunet.lot.' --
pero cualquiera que lo mire concluye que sigue mal, y por eso el tema se siente
sin resolver aunque opere bien.

Dos cosas:
1. El code de la activa pasa a amunet.lot.BHE01.1000, para que no quede rastro
   contradictorio.
2. Las tres huerfanas se DESACTIVAN, no se borran: asi queda el historial de que
   existieron, que es lo que pide la trazabilidad.

NO se toca el lote HEB01082601: esta liberado y el candado de calidad impide
renombrarlo. Ese nombre se queda para siempre, y es correcto.
"""
SEQ = env['ir.sequence'].sudo(); T = env['product.template'].sudo()
p = env['product.product'].sudo().search([('default_code','=','STBHE01')], limit=1)
activa = p.product_tmpl_id.lot_sequence_id
print('   secuencia activa: id=%s  prefix=%s' % (activa.id, activa.prefix))

if activa.code and 'HEB01' in activa.code:
    antes = activa.code
    activa.write({'code': antes.replace('HEB01','BHE01')})
    print('      code corregido: %s -> %s' % (antes, activa.code))
else:
    print('      code ya estaba bien: %s' % activa.code)
assert activa.code.startswith('amunet.lot.'), 'se rompio el patron amunet.lot.'
print('      sigue siendo secuencia Amunet: %s' % p.product_tmpl_id._is_amunet_auto_lot_enabled())

print('')
print('   huerfanas a desactivar:')
todas = SEQ.search(['|',('prefix','like','HEB'),('prefix','like','BHE')])
for s in todas:
    usan = T.search([('lot_sequence_id','=',s.id)])
    if usan:
        print('      id=%-5s la usa %s, se deja' % (s.id, ', '.join(usan.mapped('default_code'))))
        continue
    if not s.active:
        print('      id=%-5s ya estaba desactivada' % s.id); continue
    s.write({'active': False})
    print('      id=%-5s prefix=%-22s desactivada (%s)' % (s.id, s.prefix, s.name[:40]))
env.flush_all(); env.cr.commit()
print('')
print('   === como queda:')
for s in SEQ.with_context(active_test=False).search(['|',('prefix','like','HEB'),('prefix','like','BHE')]):
    usan = T.search([('lot_sequence_id','=',s.id)])
    print('      id=%-5s prefix=%-22s activa=%-6s code=%-26s usada por: %s' % (
        s.id, s.prefix, s.active, s.code or '-',
        ', '.join(usan.mapped('default_code')) if usan else 'nadie'))
