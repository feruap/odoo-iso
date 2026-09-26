# -*- coding: utf-8 -*-
"""Corregir el prefijo invertido de la secuencia de STBHE01: HEB01 -> BHE01.

Reportado por Karla (25-sep-2026): el lote HEB01082601 tiene el nombre al reves.
El error no esta en el lote sino en la SECUENCIA del producto, cuyo prefijo dice
HEB01: el lote salio asi solo. STBHE01 es el unico de su familia con el prefijo
invertido -- STBAC01 da BAC01, STBHB01 da BHB01, STBPR01 da BPR01 -- y la regla
de la casa es la clave sin las dos primeras letras, o sea BHE01.

EL LOTE EXISTENTE NO SE RENOMBRA. Esta LIBERADO, y el candado de calidad lo
impide: "No se pueden modificar campos criticos de un lote liberado (name). Cree
un reanalisis o registre una desviacion/CAPA si necesita cambiar el expediente."
Ese candado es correcto: el nombre del lote esta en su certificado de analisis y
en las etiquetas de las 985 piezas que hay en el anaquel. Cambiarlo por consola
dejaria el expediente diciendo una cosa y el papel otra. Si hay que corregirlo,
lo decide Calidad por la via de la desviacion.

Se corrige la secuencia -- del proximo lote en adelante saldra BHE01 -- y se deja
la nota en el lote viejo, que si se puede escribir en el chatter.
"""
P = env['product.product'].sudo(); L = env['stock.lot'].sudo()
p = P.search([('default_code','=','STBHE01')], limit=1)
assert p, 'no existe STBHE01'
t = p.product_tmpl_id
s = t.lot_sequence_id
if s and 'HEB01' in (s.prefix or ''):
    antes_p, antes_n = s.prefix, s.name
    s.write({'prefix': antes_p.replace('HEB01','BHE01'),
             'name': (antes_n or '').replace('HEB01','BHE01')})
    print('   secuencia corregida')
    print('      prefijo: "%s" -> "%s"' % (antes_p, s.prefix))
    print('      nombre:  "%s"' % s.name)
else:
    print('   la secuencia ya estaba correcta: %s' % (s.prefix if s else 'ninguna'))
t.invalidate_recordset()
print('      prefijo visible en la ficha: %s' % (t.amunet_lot_prefix or '-'))
print('      proximo lote saldra como: BHE01' + '0926' + '01')

l = L.search([('name','=','HEB01082601')], limit=1)
if l:
    ex = sum(env['stock.quant'].sudo().search([('lot_id','=',l.id)]).mapped('quantity'))
    print('')
    print('   lote existente: %s   liberado=%s   existencia=%s' % (
        l.name, l.amunet_lot_release_state, ex))
    print('      NO se renombra: el candado de lote liberado lo impide')
    l.message_post(body=(
        'Karla reportó que este nombre está invertido: por la nomenclatura de la '
        'casa debería ser <b>BHE01082601</b>, no HEB01082601. El origen era la '
        'secuencia del producto, que tenía el prefijo HEB01 en lugar de BHE01; '
        'ya se corrigió, así que <b>del próximo lote en adelante saldrá BHE01</b>.'
        '<br/><br/>Este lote <b>conserva su nombre</b>: está liberado y el candado '
        'de calidad no permite cambiarle el nombre sin una desviación. Es lo '
        'correcto, porque el nombre está en su certificado de análisis y en las '
        'etiquetas de las piezas que hay en el anaquel. Si se decide corregirlo, '
        'debe ir por la vía de la desviación, no por captura.'))
    print('      nota asentada en el chatter del lote')
env.flush_all(); env.cr.commit()
print('   LISTO')
