# -*- coding: utf-8 -*-
"""Los 8 apuntes de Mery que quedaron listos para aplicar.

Mery reviso el panorama del catalogo y encontro cinco duplicados que el cruce
por nombre no habia visto, porque los nombres no se parecen como texto:
"Bascula de precision Rhino" contra "Balanza semianalitica digital",
"Cubrezapatos" contra "Zapatones". Hizo falta su ojo.

TRES FUSIONES. La ficha del catalogo cede su liga, su imagen y la casilla de
publicado al producto real, y se borra. Mery pidio borrar y no archivar para
que nadie sin contexto se vuelva a confundir.
  Bascula de precision Rhino        -> EQBSD01  Balanza semianalitica digital
  Base caldo Half Fraser 500 g      -> MPREC29  Medio de cultivo Fraser
  Cubrezapatos desechables          -> COZAP01  Zapatones

  El par de Half Fraser resuelve ademas lo de MPREC100: ya no hace falta
  ampliar el consecutivo a tres digitos, que rompia la normativa.

DOS BORRADOS, sin producto real detras:
  Centrifuga para laboratorio  -- "ya no se compra desde aqui"
  Varilla agitadora magnetica  -- "la compra estuvo mal"

TRES ALTAS. Aqui SI se crea producto, con clave, porque no existe equivalente:
  Escuadra profesional 9 cm     -> COESC01
  Puntero laser verde           -> COPLA01
  Tijeras para zurdos 21 cm     -> COTIJ01  (se comprobo: no hay ninguna tijera
                                             en el catalogo)

Idempotente. DRY_RUN=True no escribe.
"""
DRY_RUN = False

FUSIONES = [
    ('Báscula de precisión Rhino', 'EQBSD01'),
    ('Base caldo Half Fraser granulado 500 g', 'MPREC29'),
    ('Cubrezapatos desechables', 'COZAP01'),
]
BORRAR = ['Centrífuga para laboratorio', 'Varilla agitadora magnética']
ALTAS = [
    ('Escuadra profesional 9 cm sin bisel', 'COESC01', 'Escuadra profesional 9 cm sin bisel'),
    ('Puntero láser verde recargable', 'COPLA01', 'Puntero láser verde recargable'),
    ('Tijeras para zurdos 21 cm', 'COTIJ01', 'Tijeras para zurdos 21 cm'),
]

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id, context=dict(env.context, amunet_alta_autorizada=True))
PT = env['product.template']

ATADURAS = [('movimientos','stock.move'), ('existencia','stock.quant'),
            ('recetas','mrp.bom.line'), ('compras','purchase.order.line'),
            ('solicitudes de compra','amunet.solicitud.compra.line'),
            ('solicitudes de material','amunet.material.request.line')]

def ficha(nombre):
    for lang in ('es_MX', 'en_US'):
        f = PT.with_context(lang=lang).search([('name', '=', nombre)])
        f = f.filtered(lambda t: t.marketplace_enabled and not t.product_variant_id.default_code)
        if len(f) == 1:
            return f
        assert len(f) <= 1, 'hay %d fichas "%s"' % (len(f), nombre)
    return PT.browse()

def sin_usar(f):
    for etiqueta, modelo in ATADURAS:
        n = env[modelo].sudo().search_count([('product_id.product_tmpl_id', '=', f.id)])
        assert not n, '"%s" tiene %d %s: NO se toca' % (f.name, n, etiqueta)

fus, bor, alt, avisos = [], [], [], []

for nombre, clave in FUSIONES:
    real = env['product.product'].search([('default_code', '=', clave)], limit=1)
    assert real, 'no existe %s' % clave
    f = ficha(nombre)
    if not f:
        avisos.append((nombre, 'ya no esta en el catalogo')); continue
    sin_usar(f)
    t = real.product_tmpl_id
    vals = {'marketplace_enabled': True,
            'marketplace_flow': 'general',
            'marketplace_purchase_url': f.marketplace_purchase_url or t.marketplace_purchase_url}
    if f.image_1920 and not t.image_1920:
        vals['image_1920'] = f.image_1920
    nombre_real = t.name
    if not DRY_RUN:
        t.write(vals)
        f.unlink()
    fus.append((nombre, clave, nombre_real))

for nombre in BORRAR:
    f = ficha(nombre)
    if not f:
        avisos.append((nombre, 'ya no esta en el catalogo')); continue
    sin_usar(f)
    if not DRY_RUN:
        f.unlink()
    bor.append(nombre)

for nombre, clave, nombre_final in ALTAS:
    ya = env['product.product'].search([('default_code', '=', clave)], limit=1)
    if ya:
        avisos.append((clave, 'la clave ya existe: %s' % ya.name)); continue
    f = ficha(nombre)
    if not f:
        avisos.append((nombre, 'ya no esta en el catalogo')); continue
    if not DRY_RUN:
        # La ficha YA es un product.template: solo se le pone clave y nombre
        # definitivo. No se crea uno nuevo ni se duplica nada.
        f.write({'default_code': clave, 'marketplace_flow': 'general'})
        f.with_context(lang='es_MX').name = nombre_final
    alt.append((clave, nombre_final))

if not DRY_RUN:
    env.cr.commit()

print('=' * 84)
print('SIMULACION — no se escribio nada' if DRY_RUN else 'APLICADO')
print('-' * 84)
for n, c, r in fus: print('  FUSION   %-40s -> %-9s %s' % (n[:40], c, r[:28]))
for n in bor:       print('  BORRADA  %s' % n)
for c, n in alt:    print('  ALTA     %-9s %s' % (c, n))
if avisos:
    print('-' * 84)
    for q, m in avisos: print('  [!] %-40s %s' % (q[:40], m))
print('-' * 84)
print('  fusiones %d | borradas %d | altas %d' % (len(fus), len(bor), len(alt)))
print('=' * 84)
