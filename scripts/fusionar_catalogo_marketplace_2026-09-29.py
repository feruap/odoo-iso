# -*- coding: utf-8 -*-
"""Unir las fichas del catalogo interno con el producto real que ya existe.

EL PROBLEMA. El catalogo del Marketplace no se armo prendiendo la casilla en
productos que ya existian: se armo el 26-jul importando un CSV que CREO 60
productos nuevos, sin clave y sin pasar por la normativa de codificacion. De
esos, 15 duplican material que Amunet ya tenia dado de alta y con existencia:
"Agar bacteriologico 450 g" se creo cinco dias despues de MPREC90 "Agar
bacteriologico", que tiene 418 g en el almacen y 12 movimientos.

Consecuencia: quien pide del catalogo genera una compra contra la ficha
vacia, y los 418 g que hay siguen sin que nadie los vea, porque cuelgan del
otro producto.

QUE HACE. Por cada par: pasa al producto REAL lo que la ficha tenia de
escaparate (liga de compra, imagen, flujo), le prende la casilla, y BORRA la
ficha. Mery pidio borrar y no archivar, para que manana nadie sin contexto se
vuelva a confundir.

POR QUE SE PUEDE BORRAR. Las 15 fichas no se han usado NUNCA: cero
movimientos, cero existencia, cero recetas, cero ordenes de compra, cero
solicitudes. No hay nada que migrar. Tampoco hay referencias xml, lineas de
proveedor ni reglas de reabastecimiento, y el CSV semilla no esta en el
manifest, asi que no se vuelven a crear al actualizar el modulo.

DOS DECISIONES DE MERY:
  - Azida: la ficha NO corresponde a SPSAS01 (que es la solucion al 20%) sino
    a MPREC07, el reactivo puro. Lo confirma la receta: SPSAS01 se fabrica con
    200 g de MPREC07.
  - Agua peptonada: DOS fichas para un mismo producto, MPREC28. No hay codigo
    de proveedor, se compra en linea por dos ligas distintas; el campo de liga
    admite una sola, asi que la segunda va en la nota que ve quien pide.

Probeta 10 ml y Jeringa de vidrio se quedan fuera: Mery dijo que NO son las
mismas, asi que siguen como altas nuevas por codificar.

Idempotente. DRY_RUN=True no escribe nada.
"""
DRY_RUN = False

# nombre de la ficha (como esta en el catalogo) -> clave del producto real
PARES = [
    ('Agar bacteriológico 450 g', 'MPREC90'),
    ('Azul de bromofenol 5 g', 'MPREC60'),
    ('Agua peptonada amortiguada 450 g McdLab', 'MPREC28'),
    ('Agar sangre base 100 g', 'MPREC91'),
    ('Agar Mueller Hinton 38 g para 1 L', 'MPREC88'),
    ('Azida de sodio 100 g', 'MPREC07'),
    ('Autoclave esterilizador 24 L', 'EQEPV01'),
    ('Rack de puntas amarillas estériles', 'CORAC01'),
    ('Colorante amarillo 5 laca alumínica 500 g', 'MPREC55'),
    ('Gel refrigerante frigogel', 'STGEL01'),
    ('Mechero o lámpara de alcohol de vidrio', 'EQLAA01'),
    ('Solución para electrodos pH 3M KCl', 'MPREC83'),
    ('Tubo para PCR 30 bolsas', 'COTUB01'),
    ('Tubo de centrífuga 10 ml', 'COTUB05'),
]
# La segunda ficha del agua peptonada: su liga se conserva en la nota y se borra.
SEGUNDA_AGUA = 'Agua peptonada amortiguada 100 g'

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id, context=dict(env.context, amunet_alta_autorizada=True))
PT = env['product.template']

ATADURAS = [
    ('movimientos', 'stock.move', 'product_id.product_tmpl_id'),
    ('existencia', 'stock.quant', 'product_id.product_tmpl_id'),
    ('recetas', 'mrp.bom.line', 'product_id.product_tmpl_id'),
    ('compras', 'purchase.order.line', 'product_id.product_tmpl_id'),
    ('solicitudes de compra', 'amunet.solicitud.compra.line', 'product_id.product_tmpl_id'),
    ('solicitudes de material', 'amunet.material.request.line', 'product_id.product_tmpl_id'),
]


def ficha(nombre):
    """La ficha del catalogo, buscada por nombre en cualquier idioma."""
    for lang in ('es_MX', 'en_US'):
        f = PT.with_context(lang=lang).search([('name', '=', nombre)])
        f = f.filtered(lambda t: t.marketplace_enabled and not t.product_variant_id.default_code)
        if len(f) == 1:
            return f
        assert len(f) <= 1, 'Hay %d fichas llamadas "%s"' % (len(f), nombre)
    return PT.browse()


def sin_usar(f):
    """Se niega a borrar cualquier ficha que tenga algo colgando."""
    for etiqueta, modelo, campo in ATADURAS:
        n = env[modelo].sudo().search_count([(campo, '=', f.id)])
        assert not n, '"%s" tiene %d %s: NO se toca' % (f.name, n, etiqueta)


hechos, ya, faltantes = [], [], []

# --- la nota con las dos ligas del agua peptonada -------------------------
f2 = ficha(SEGUNDA_AGUA)
liga2 = f2.marketplace_purchase_url if f2 else ''

for nombre, clave in PARES:
    real = env['product.product'].search([('default_code', '=', clave)], limit=1)
    assert real, 'No existe el producto real %s' % clave
    f = ficha(nombre)
    if not f:
        (ya if real.product_tmpl_id.marketplace_enabled else faltantes).append((nombre, clave))
        continue
    sin_usar(f)
    t = real.product_tmpl_id
    vals = {
        'marketplace_enabled': True,
        # El flujo NO se hereda: 9 de las 14 fichas venian en 'production', y ese
        # flujo obliga a que el material se pida contra una orden de fabricacion.
        # Pegarselo al producto real dejaria sin poder pedirse a una autoclave o a
        # un rack de puntas. Mery, 29-sep: las 14 entran en 'general'.
        'marketplace_flow': 'general',
        'marketplace_purchase_url': f.marketplace_purchase_url or t.marketplace_purchase_url,
    }
    if f.image_1920 and not t.image_1920:
        vals['image_1920'] = f.image_1920
    if clave == 'MPREC28' and liga2:
        vals['marketplace_request_note'] = (
            'Se compra en línea, no tiene código de proveedor. Dos presentaciones:\n'
            '450 g McdLab: %s\n100 g: %s' % (f.marketplace_purchase_url or '-', liga2))
    # El flujo se lee ANTES de borrar: despues la ficha ya no existe.
    flujo_previo = f.marketplace_flow or '-'
    nombre_real = t.name
    if not DRY_RUN:
        t.write(vals)
        f.unlink()
    hechos.append((nombre, clave, nombre_real, '%s -> general' % flujo_previo))

# la segunda ficha del agua ya cedio su liga: se borra
borrada2 = False
if f2:
    sin_usar(f2)
    if not DRY_RUN:
        f2.unlink()
    borrada2 = True

if not DRY_RUN:
    env.cr.commit()

print('=' * 92)
print('SIMULACION — no se escribio nada' if DRY_RUN else 'APLICADO')
print('-' * 92)
for nombre, clave, real, flujo in hechos:
    print('  %-42s -> %-9s %-30s [%s]' % (nombre[:42], clave, real[:30], flujo))
if borrada2:
    print('  %-42s -> su liga pasa a la nota de MPREC28 y se borra' % SEGUNDA_AGUA[:42])
print('-' * 92)
print('  a unir: %d fichas | ya estaban: %s | no encontradas: %s' % (
    len(hechos), [c for _, c in ya] or 'ninguna', [c for _, c in faltantes] or 'ninguna'))
print('=' * 92)
