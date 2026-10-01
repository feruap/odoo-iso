# -*- coding: utf-8 -*-
"""Las ultimas 4 fichas duplicadas del catalogo interno: 3 se unen, 1 va a propuestas.

DE DONDE VIENE. El catalogo del Marketplace se sembro el 26-jul importando un CSV
que CREO productos nuevos en vez de prender la casilla en los que ya existian.
Resultado: quien pedia del catalogo generaba la compra contra una ficha vacia,
mientras el material real seguia colgado del otro producto y nadie lo veia.

Se limpiaron 18. Quedaban cuatro que no se podian decidir sin ver el material
fisico. Patricia (RRHH) las resolvio el 30-sep:

    Esponja facial de celulosa 12 piezas       -> es STESP01
    Hielera de unicel No. 4                    -> es STHIE01 (Hielera chica)
    Tubo PCR 0.2 ml tapa plana MUHWA           -> es COTUB01
    Bote de residuos peligrosos 21 L           -> es NUEVO, no es COCRP01

EL BOTE NO SE DA DE ALTA. Mery, 01-oct: no se codifica hasta que exista un pedido
real de ese material. Nadie lo ha pedido -- la ficha venia del CSV sembrado, no de
una solicitud-, asi que su ficha se borra y queda registrado como PROPUESTA en
estado 'submitted', que es donde vive lo que todavia nadie necesita. Si manana
alguien lo pide, se aprueba la propuesta y se codifica entonces.

LA PRESENTACION VA EN LA NOTA, y esto es lo que evita un error de pedido: dos de
las tres fichas son presentaciones, no piezas. La del tubo es bolsa de 1000 y
COTUB01 se maneja por pieza; la de la esponja es paquete de 12 y STESP01 tambien va
por pieza. Sin aviso, quien pide "1" no sabe si le llega 1 tubo o 1000. En vez de
cambiar unidades -- que afectaria 19,000 piezas de existencia y 27 movimientos- se
escribe la presentacion en la nota que ve quien pide.

EL FLUJO ENTRA COMO 'general' A PROPOSITO: la ficha del tubo viene en 'production',
y ese flujo obliga a pedir el material contra una orden de fabricacion. Pegarselo a
COTUB01 dejaria sin poder pedirse un tubo para cualquier otra cosa. Mismo criterio
que el 29-sep con las 14 anteriores.

Las fichas se BORRAN, no se archivan (decision de Mery el 29-sep): una ficha
archivada reaparece en busquedas y manana alguien sin contexto se vuelve a confundir.
Antes de borrar se comprueba que no tengan NADA colgando.

Idempotente. DRY_RUN=True no escribe nada.
"""
DRY_RUN = False

PARES = [
    ('Esponja facial de celulosa 12 piezas', 'STESP01',
     'Se compra en PAQUETE DE 12 ESPONJAS. El producto se maneja por pieza: al pedir, '
     'indica cuantas piezas necesitas, no cuantos paquetes.'),
    ('Hielera de unicel No. 4', 'STHIE01', ''),
    ('Tubo PCR 0.2 ml tapa plana (MUHWA 1000 pz/bolsa)', 'COTUB01',
     'Se compra en BOLSA DE 1000 PIEZAS (tapa plana, marca MUHWA). El producto se maneja '
     'por pieza: al pedir, indica cuantas piezas necesitas, no cuantas bolsas.'),
]
FICHA_NUEVA = 'Bote de residuos peligrosos 21 L'

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
    ('propuestas', 'amunet.marketplace.product.proposal', 'product_tmpl_id'),
]


def ficha(nombre):
    """La ficha del catalogo: sin clave y habilitada en el Marketplace."""
    for lang in ('es_MX', 'en_US'):
        f = PT.with_context(lang=lang).search([('name', '=', nombre)])
        f = f.filtered(lambda t: t.marketplace_enabled and not t.product_variant_id.default_code)
        if len(f) == 1:
            return f
        assert len(f) <= 1, 'Hay %d fichas llamadas "%s"' % (len(f), nombre)
    return PT.browse()


def sin_usar(f):
    for etiqueta, modelo, campo in ATADURAS:
        n = env[modelo].sudo().search_count([(campo, '=', f.id)])
        assert not n, '"%s" tiene %d %s: NO se toca' % (f.name, n, etiqueta)


hechos, ya = [], []
for nombre, clave, nota in PARES:
    real = env['product.product'].search([('default_code', '=', clave)], limit=1)
    assert real, 'No existe el producto real %s' % clave
    t = real.product_tmpl_id
    f = ficha(nombre)
    if not f:
        ya.append((nombre, clave, t.marketplace_enabled))
        continue
    sin_usar(f)
    vals = {'marketplace_enabled': True, 'marketplace_flow': 'general',
            'marketplace_purchase_url': f.marketplace_purchase_url or t.marketplace_purchase_url}
    if f.image_1920 and not t.image_1920:
        vals['image_1920'] = f.image_1920
    if nota:
        previa = (t.marketplace_request_note or '').strip()
        vals['marketplace_request_note'] = nota if not previa or nota in previa else previa + '\n' + nota
    flujo_previo = f.marketplace_flow or '-'
    liga_ficha = f.marketplace_purchase_url or ''
    liga_real = t.marketplace_purchase_url or ''
    if clave == 'COTUB01' and liga_real and liga_ficha and liga_real != liga_ficha:
        # el campo admite una sola liga: la otra se conserva en la nota
        vals['marketplace_purchase_url'] = liga_real
        vals['marketplace_request_note'] = (vals.get('marketplace_request_note') or '') + \
            '\nOtra liga de compra (MUHWA, bolsa de 1000): %s' % liga_ficha
    if not DRY_RUN:
        t.write(vals)
        f.unlink()
    hechos.append((nombre, clave, t.name, '%s -> general' % flujo_previo, bool(nota)))

# --- el bote: a propuestas, sin codificar ---
prop_hecha = None
f = ficha(FICHA_NUEVA)
ya_prop = env['amunet.marketplace.product.proposal'].search([('name', 'ilike', 'residuos peligrosos 21')], limit=1)
if ya_prop:
    prop_hecha = 'ya existia la propuesta id=%s (%s)' % (ya_prop.id, ya_prop.state)
elif f:
    sin_usar(f)
    rrhh = env['res.users'].search([('login', '=', 'rrhh@amunet.com.mx')], limit=1) or mery
    vals = {
        'name': FICHA_NUEVA,
        'state': 'submitted',
        'request_type': 'general',
        'supply_type': 'comprado',
        'requester_id': rrhh.id,
        'category_id': f.categ_id.id,
        'purchase_url': f.marketplace_purchase_url or '',
        'justification': (
            'Producto NUEVO: no corresponde a COCRP01 (Contenedor RPBI para liquidos), '
            'confirmado por Patricia/RRHH el 30-sep-2026 tras ver el material.\n\n'
            'NO se codifica todavia. Decision de Mery el 01-oct-2026: no se da de alta '
            'hasta que exista un pedido real de este material. Nadie lo ha pedido -- la '
            'ficha venia del CSV con que se sembro el catalogo el 26-jul-2026, no de una '
            'solicitud-, por eso queda aqui en vez de en el catalogo.\n\n'
            'Si alguien lo pide: aprobar esta propuesta, pedir clave a Documentacion y '
            'darlo de alta como producto nuevo.'),
    }
    if not DRY_RUN:
        p = env['amunet.marketplace.product.proposal'].create(vals)
        f.unlink()
        prop_hecha = 'propuesta creada id=%s, ficha del catalogo borrada' % p.id
else:
    prop_hecha = 'no se encontro la ficha del bote (ya se habia quitado?)'

if not DRY_RUN:
    env.cr.commit()

print('=' * 94)
print('SIMULACION -- no se escribio nada' if DRY_RUN else 'APLICADO')
print('-' * 94)
for nombre, clave, real, flujo, con_nota in hechos:
    print('  %-46s -> %-8s %-24s [%s]%s' % (nombre[:46], clave, real[:24], flujo,
                                            '  + nota de presentacion' if con_nota else ''))
if ya:
    for nombre, clave, en_cat in ya:
        print('  %-46s -> %-8s ya estaba unido (en catalogo: %s)' % (nombre[:46], clave, en_cat))
print('  %-46s -> %s' % (FICHA_NUEVA[:46], prop_hecha))
print('-' * 94)

print('\n=== COMPROBACION ===')
for _, clave, _ in PARES:
    t = env['product.product'].search([('default_code', '=', clave)], limit=1).product_tmpl_id
    print('  %-8s en catalogo=%-5s flujo=%-8s liga=%s' % (
        clave, t.marketplace_enabled, t.marketplace_flow, 'si' if t.marketplace_purchase_url else 'no'))
    if t.marketplace_request_note:
        for linea in t.marketplace_request_note.strip().split('\n'):
            print('           nota: %s' % linea[:80])
# product_variant_id NO es un campo almacenado: en un search() truena. Se filtra en Python.
quedan = PT.search([('marketplace_enabled', '=', True)]).filtered(
    lambda t: not t.product_variant_id.default_code)
print('\n  fichas del catalogo SIN clave que quedan: %s%s' % (
    len(quedan), (' -> ' + ', '.join(q.name or '?' for q in quedan))[:140] if quedan else ''))
