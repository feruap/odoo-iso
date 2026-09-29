# -*- coding: utf-8 -*-
"""MPREC61 Glicina: dejar 'acido aminoacetico' visible en la ficha.

Karla lo pidio el 25-sep: quien ve el frasco no siempre reconoce el nombre,
y el proveedor lo etiqueta con el sinonimo. Va en la descripcion, que es lo
que se ve en la ficha y en los documentos.

De paso se escribe el nombre en es_MX. Los dos productos tenian el nombre
solo en en_US: la interfaz en espanol se apoya en el ingles cuando falta, asi
que se veia bien, pero cualquier cosa que lea es_MX lo encuentra vacio.
"""
from markupsafe import Markup

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

p = env['product.product'].search([('default_code', '=', 'MPREC61')], limit=1)
assert p, 'No existe MPREC61'
t = p.product_tmpl_id

nombre = t.with_context(lang='en_US').name
t.with_context(lang='es_MX').name = nombre
t.with_context(lang='es_MX').description = Markup(
    '<p>También conocido como <b>ácido aminoacético</b>. '
    'El proveedor lo etiqueta con ese nombre.</p>')
env.cr.commit()

print('%s | es_MX="%s" | descripcion: %s' % (
    p.default_code, t.with_context(lang='es_MX').name,
    (t.with_context(lang='es_MX').description or '')[:70]))
