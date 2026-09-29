"""Cierra el caso P00214: deja el rastro y hace imposible confundir los dos combos.

Autorizado por Mery el 29-sep-2026.

EL CASO: la orden P00214 pidio el combo I204-4025, de TRES hojas, y llego el
I163-4045, de CUATRO. La receta del Combo Mosquito terminado (DMDCZ01) consume las
CUATRO, asi que con el de tres no se puede fabricar: el error estuvo en el pedido.

Lo que llego se acepto y los 900 cm de la hoja de Dengue ya se dieron de alta
(28-sep). Falta cerrar el circulo para que no se repita.

QUIEN LO PIDIO: la orden y su linea las creo OdooBot, o sea un proceso automatico,
no una persona. Por eso la prevencion tiene que estar en el CATALOGO: el nombre de
cada combo debe decir para que producto sirve, no solo que hojas trae.

QUE HACE:
  1. Anota en la orden P00214 lo que paso, para que quede en su historial.
  2. Deja el nombre de cada combo diciendo a que producto alimenta, en los dos
     idiomas. El I163 no tenia nombre en espanol, solo en ingles.

No toca precios ni nada de la orden: solo el historial y el nombre de los productos.

Idempotente.
"""
from markupsafe import Markup

PT = env['product.template'].sudo()
PO = env['purchase.order'].sudo()

NOMBRES = {
    'I163-4045': ('COMBO MOSQUITO Dengue/Zika/Chikungunya — 4 hojas (SPHMC85 + '
                  'SPHMC86 + SPHMC87 + SPHMC88) — ES EL QUE USA EL COMBO MOSQUITO '
                  'DMDCZ01'),
    'I204-4025': ('COMBO Zika/Chikungunya — 3 hojas (SPHMC86 + SPHMC87 + SPHMC88) — '
                  'NO SIRVE PARA DMDCZ01: le falta la hoja de Dengue'),
}

print('-- 1. el historial de la orden --')
po = PO.search([('name', '=', 'P00214')], limit=1)
if not po:
    print('   [ojo] no existe la orden P00214')
else:
    ya = env['mail.message'].sudo().search_count([
        ('model', '=', 'purchase.order'), ('res_id', '=', po.id),
        ('body', 'like', 'combo que llego')])
    if ya:
        print('   [ya] la orden ya tiene la anotacion')
    else:
        po.message_post(body=Markup(
            'Aclaracion de trazabilidad, 29-sep-2026, autorizada por Mery.<br/><br/>'
            'En esta orden se pidio el combo <b>I204-4025</b> (tres hojas: SPHMC86, '
            '87 y 88) y el <b>combo que llego</b> fue el <b>I163-4045</b> (cuatro '
            'hojas: incluye SPHMC85 de Dengue). Se recibio y registro como I204-4025, '
            'asi que la conversion CONV/00010 genero solo tres hojas y la de Dengue se '
            'quedo sin dar de alta hasta el 28-sep.<br/><br/>'
            '<b>El error estuvo en el pedido, no en la entrega:</b> la receta del '
            'Combo Mosquito terminado (DMDCZ01) consume las CUATRO hojas, 0.40 cm de '
            'cada una, asi que con el combo de tres no se puede fabricar. Mery acepto '
            'el material como llego.<br/><br/>'
            'Esta orden y su linea las creo un proceso automatico (OdooBot). Para que '
            'no se repita, el nombre de los dos combos ahora dice a que producto '
            'alimenta cada uno.'))
        print('   [ok] anotacion puesta en P00214')

print('\n-- 2. los nombres de los dos combos --')
for clave, nombre in NOMBRES.items():
    t = PT.search([('default_code', '=', clave)], limit=1)
    if not t:
        print('   [ojo] no existe %s' % clave); continue
    actual_en = t.with_context(lang='en_US').name or ''
    actual_es = t.with_context(lang='es_MX').name or ''
    if actual_es == nombre and actual_en == nombre:
        print('   [ya] %s ya tiene el nombre nuevo' % clave); continue
    # se escribe en los DOS idiomas: el I163 no tenia nombre en espanol y el
    # usuario en es_MX veria el ingles por respaldo
    t.with_context(lang='en_US').write({'name': nombre})
    t.with_context(lang='es_MX').write({'name': nombre})
    print('   [ok] %s' % clave)
    print('        antes (es): %s' % (actual_es[:72] or '(vacio)'))
    print('        ahora     : %s' % nombre[:72])
    t.message_post(body=Markup(
        'Nombre aclarado el 29-sep-2026: ahora dice a que producto alimenta este '
        'combo, no solo que hojas trae. Se cambio porque la orden P00214 pidio el '
        'combo equivocado -- el de tres hojas para un producto que necesita cuatro -- '
        'y la eligio un proceso automatico.'))

print('\n=== como quedan ===')
for clave in NOMBRES:
    t = PT.search([('default_code', '=', clave)], limit=1)
    if not t: continue
    print('   %-11s %s' % (clave, t.with_context(lang='es_MX').name))
env.cr.commit()
