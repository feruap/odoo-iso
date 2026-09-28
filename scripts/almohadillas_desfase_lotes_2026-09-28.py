"""Almohadillas SPALMA11/12/13: el lote de cada una llevaba el numero de la anterior.

Autorizado por Mery el 28-sep-2026: si existe un desfase, se ajusta.

EL DESFASE, los tres del 12-mar-2026:

    SPALMA11   ALMA10032601   ->   ALMA11032601
    SPALMA12   ALMA11032601   ->   ALMA12032601
    SPALMA13   ALMA12032601   ->   ALMA13032601

Cada lote lleva el numero de la almohadilla ANTERIOR: se arrastro una posicion al
darlas de alta seguidas. Lo confuso era que ALMA11032601 existia dos veces -- como
lote de SPALMA12 y como el nombre que le tocaba a SPALMA11 --, pero no estorba: el
nombre de lote es unico POR PRODUCTO, no en todo el sistema.

Los tres estan SIN EXISTENCIA y sus analisis (QC/2026/00357, 00358 y 00359) siguen
en BORRADOR, asi que no se toca nada liberado.

Idempotente.
"""

Lot = env['stock.lot'].sudo()
Check = env['amunet.quality.check'].sudo()
PT = env['product.template'].sudo()

DESFASE = [('SPALMA11', 'ALMA10032601', 'ALMA11032601'),
           ('SPALMA12', 'ALMA11032601', 'ALMA12032601'),
           ('SPALMA13', 'ALMA12032601', 'ALMA13032601')]

for clave, viejo, nuevo in DESFASE:
    prod = env['product.product'].sudo().search([('default_code', '=', clave)], limit=1)
    if not prod:
        print('[ojo] %s no existe en esta base' % clave); continue
    lote = Lot.search([('name', '=', viejo), ('product_id', '=', prod.id)], limit=1)
    if not lote:
        ya = Lot.search([('name', '=', nuevo), ('product_id', '=', prod.id)], limit=1)
        print('[%s] %s: %s' % ('ya' if ya else 'ojo', clave,
                               'ya se llama %s' % nuevo if ya
                               else 'no encontre el lote %s' % viejo))
        continue
    # guarda: nada liberado
    liberados = Check.search([('lot_id', '=', lote.id)]).filtered(
        lambda c: c.state == 'done' or c.user_authorized_id)
    if liberados:
        print('NO SE TOCA %s: su analisis %s esta liberado' % (
            clave, ', '.join(liberados.mapped('name'))))
        continue
    existencia = sum(env['stock.quant'].sudo().search([
        ('lot_id', '=', lote.id), ('location_id.usage', '=', 'internal')]).mapped('quantity'))
    lote.write({'name': nuevo})
    lote.message_post(body=(
        'Lote renombrado de %s a %s el 28-sep-2026, autorizado por Mery.<br/><br/>'
        'Los lotes de las tres almohadillas pretratadas se capturaron corridos una '
        'posicion: cada uno llevaba el numero de la almohadilla anterior. Este lote '
        'es de %s, asi que le corresponde el prefijo ALMA%s. Sin existencia y con su '
        'analisis en borrador al momento de corregirlo.'
    ) % (viejo, nuevo, clave, clave[-2:]))
    print('[ok] %s: %s -> %s   (existencia %g)' % (clave, viejo, nuevo, existencia))
    for qc in Check.search([('lot_id', '=', lote.id)]):
        if (qc.lot_amunet or '') == nuevo:
            continue
        try:
            vals = {'lot_amunet': nuevo}
            if qc.state != 'draft':
                vals['change_reason'] = ('Correccion del desfase en el nombre del '
                                         'lote: %s -> %s' % (viejo, nuevo))
            qc.write(vals)
            print('     %s: nombre del lote actualizado' % qc.name)
        except Exception as e:
            print('     %s: no se pudo actualizar -> %s' % (qc.name, str(e)[:100]))

print('\n=== como quedan ===')
for clave, _, _ in DESFASE:
    prod = env['product.product'].sudo().search([('default_code', '=', clave)], limit=1)
    if not prod: continue
    for l in Lot.search([('product_id', '=', prod.id)]):
        qcs = Check.search([('lot_id', '=', l.id)])
        print('   %-9s %-13s %s' % (clave, l.name,
                                    ', '.join('%s (%s)' % (c.name, c.state) for c in qcs)))
env.cr.commit()
