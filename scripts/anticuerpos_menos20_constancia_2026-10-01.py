# -*- coding: utf-8 -*-
"""Ocho anticuerpos movidos de 2-5 C a -20 C: dejar la constancia en el sistema.

QUE REPORTO KARLA (01-oct-2026). Ocho anticuerpos que llegaron en agosto por
AMP/IN/00364 estaban en un refrigerador a 2-5 C cuando su etiqueta pide -20 C. Se
movieron al refrigerador de Calidad, que esta a -20 C. Lo aviso por escrito "para evitar
malentendidos despues".

POR QUE ESTE SCRIPT SOLO ESCRIBE NOTAS. Se busco donde registrar la condicion de
conservacion y NO EXISTE EN NINGUNA PARTE:

  - product.template no tiene ningun campo de temperatura ni de conservacion.
  - En todo el sistema no hay un solo campo de ese tipo (solo los storage_category
    nativos de Odoo, sin usar).
  - No hay ubicaciones que distingan refrigerador de congelador: los ocho lotes estan
    en AMP/Existencias, igual que todo lo demas.

Asi que hoy el dato de "este material va a -20 C" no vive en el sistema: vive en la
etiqueta del frasco y en el correo de Karla. Si manana alguien los vuelve a meter al
refrigerador de 2-5 C, nada lo impide y nada lo detecta.

Lo que este script si puede hacer es dejar la constancia donde un auditor la buscaria:
en el historial de cada lote y de cada producto. No es el control, es el registro.

Idempotente: no repite la nota.
"""

MARCA = '[conservacion -20 C, 01-oct-2026]'

LOTES = [
    ('MPANT04', 'ANT04082601', 'Anticuerpo de captura anti-proteina N SARS-CoV-2', 'FPZ0638'),
    ('MPANT05', 'ANT05082601', 'Anticuerpo de deteccion anti-proteina N SARS-CoV-2', 'FPZ0639'),
    ('MPANT12', 'ANT12082601', 'Anticuerpo de captura anti-HbA1c', 'BRJHBAS101'),
    ('MPANT16', 'ANT16082601', 'Anticuerpo de deteccion anti-25(OH)D', 'BENVDN104'),
    ('MPANT38', 'ANT38082601', 'Anticuerpo de deteccion anti-RSV', 'FPZ0180'),
    ('MPANT39', 'ANT39082601', 'Anticuerpo de captura anti-RSV', 'FPZ0181'),
    ('MPANT65', 'ANT65082601', 'Anticuerpo de captura Anti-NT-proBNP', 'BNCBNPN128'),
    ('MPANT66', 'ANT66082601', 'Anticuerpo de deteccion Anti-NT-proBNP', 'BRJNBNPS103'),
]

NOTA_LOTE = """%s

<p>Este lote se movio de un refrigerador a <b>2-5 C</b> al refrigerador de Calidad, que
esta a <b>-20 C</b>, porque su etiqueta indica esa temperatura de conservacion.</p>

<p>Lo reporto <b>Karla (Almacen MP)</b> el 01-oct-2026. El material llego en agosto por
la recepcion <b>AMP/IN/00364</b>. Referencia del proveedor: <b>%s</b>.</p>

<p><b>Nota importante:</b> el sistema no tiene hoy ningun campo donde guardar la
temperatura de conservacion de un material, ni ubicaciones que distingan un refrigerador
de un congelador. Esta nota es la unica constancia dentro de Odoo: el dato real esta en
la etiqueta del frasco.</p>""" % (MARCA, '%s')

NOTA_PRODUCTO = """%s

<p><b>Conservar a -20 C.</b> Asi lo indica la etiqueta del proveedor (ref. %s).</p>

<p>El 01-oct-2026 el lote <b>%s</b> se encontro en un refrigerador a 2-5 C y se movio al
refrigerador de Calidad, a -20 C. Lo reporto Karla (Almacen MP).</p>

<p>Se deja escrito aqui porque el sistema no tiene un campo de temperatura de
conservacion: quien reciba este material de nuevo no tiene de donde leerlo salvo la
etiqueta.</p>"""

puestas = 0
for clave, lote_name, nombre, ref in LOTES:
    tmpl = env['product.template'].search([('default_code', '=', clave)], limit=1)
    if not tmpl:
        print('  [!] no existe el producto %s' % clave)
        continue
    lote = env['stock.lot'].search([('name', '=', lote_name),
                                   ('product_id.product_tmpl_id', '=', tmpl.id)], limit=1)

    for rec, cuerpo, etq in ((lote, NOTA_LOTE % ref if lote else '', 'lote %s' % lote_name),
                             (tmpl, NOTA_PRODUCTO % (MARCA, ref, lote_name), 'producto %s' % clave)):
        if not rec:
            print('  [!] no se encontro el %s' % etq)
            continue
        ya = env['mail.message'].search_count([('model', '=', rec._name), ('res_id', '=', rec.id),
                                              ('body', 'ilike', MARCA)])
        if ya:
            print('  ya tenia la nota: %s' % etq)
            continue
        rec.sudo().message_post(body=cuerpo)
        puestas += 1
        print('  anotado: %s' % etq)

env.cr.commit()

print('\n=== COMPROBACION ===')
print('  notas puestas: %s' % puestas)
for clave, lote_name, _n, _r in LOTES:
    tmpl = env['product.template'].search([('default_code', '=', clave)], limit=1)
    lote = env['stock.lot'].search([('name', '=', lote_name)], limit=1)
    n_t = env['mail.message'].search_count([('model', '=', 'product.template'), ('res_id', '=', tmpl.id),
                                           ('body', 'ilike', MARCA)])
    n_l = env['mail.message'].search_count([('model', '=', 'stock.lot'), ('res_id', '=', lote.id),
                                           ('body', 'ilike', MARCA)]) if lote else 0
    print('  %-9s producto=%s  lote=%s' % (clave, 'si' if n_t else 'NO', 'si' if n_l else 'NO'))
