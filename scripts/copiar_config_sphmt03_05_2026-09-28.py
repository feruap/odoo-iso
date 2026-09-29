# -*- coding: utf-8 -*-
"""SPHMT03-05: copiar la configuracion de calidad de la plantilla archivada.

EL PROBLEMA. Las variantes activas de VPH (2377), Pylorinet (2378) y TB-DxNet
(2379) nacieron el 23-sep-2026 con CERO parametros y CERO puntos de control:
esos tres productos no se pueden analizar. Las plantillas archivadas
(1507/1508/1509) si tienen la configuracion buena.

EL CUIDADO. Crear el vinculo producto-parametro por la ORM dispara
_generate_specification_configs(), que siembra UNA configuracion por cada
linea de especificacion del catalogo del parametro. Para MAVI-11 eso son 154.
El primer intento dejo 207 especificaciones por producto en vez de 10; se
revirtio entero (nada preexistia bajo esas plantillas) y se rehizo asi:

    1. se crea el vinculo y se deja que siembre
    2. se borra lo sembrado
    3. se copia UNA A UNA la configuracion real de la plantilla archivada

Asi el producto queda con lo que de verdad usa, no con el catalogo completo.

Idempotente. DRY_RUN=True no escribe.
"""
DRY_RUN = False

COPIAS = [(1507, 2377, 308), (1508, 2378, 309), (1509, 2379, 310)]

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)
REL = env['amunet.quality.parameter.product.rel']
CFG = env['amunet.quality.parameter.specification.config']

print('=' * 72)
for viejo, nuevo, punto_id in COPIAS:
    t = env['product.template'].browse(nuevo)
    clave = t.default_code
    rels_v = REL.with_context(active_test=False).search([('product_tmpl_id', '=', viejo)])
    assert rels_v, 'La plantilla archivada %s no tiene parametros' % viejo
    esperado = sum(len(rv.specification_config_ids) for rv in rels_v)

    hechos = 0
    for rv in rels_v:
        rn = REL.search([('product_tmpl_id', '=', nuevo),
                         ('parameter_id', '=', rv.parameter_id.id)], limit=1)
        if rn and len(rn.specification_config_ids) == len(rv.specification_config_ids):
            continue
        if DRY_RUN:
            hechos += len(rv.specification_config_ids)
            continue
        if not rn:
            rn = REL.create({'product_tmpl_id': nuevo,
                             'parameter_id': rv.parameter_id.id,
                             'sequence': rv.sequence})
        # fuera lo sembrado por el catalogo
        rn.specification_config_ids.unlink()
        for c in rv.specification_config_ids:
            c.copy({'product_parameter_rel_id': rn.id, 'product_tmpl_id': nuevo})
            hechos += 1

    punto = env['amunet.quality.point'].browse(punto_id)
    variante = t.product_variant_ids[:1]
    falta_punto = variante and variante not in punto.product_ids
    if falta_punto and not DRY_RUN:
        punto.write({'product_ids': [(4, variante.id)]})
    print('  %-9s esperado %d especificaciones, %s %d%s' % (
        clave, esperado, 'copiaria' if DRY_RUN else 'copiadas', hechos,
        '  + punto de control %s' % punto_id if falta_punto else ''))

if not DRY_RUN:
    env.cr.commit()

print('-' * 72)
print('ESTADO FINAL' if not DRY_RUN else 'SIMULACION (no se escribio nada)')
for viejo, nuevo, _ in COPIAS:
    t = env['product.template'].browse(nuevo)
    n_rel = REL.search_count([('product_tmpl_id', '=', nuevo)])
    n_cfg = CFG.search_count([('product_parameter_rel_id.product_tmpl_id', '=', nuevo)])
    ref = CFG.search_count([('product_parameter_rel_id.product_tmpl_id', '=', viejo)])
    print('  %-9s parametros=%d especificaciones=%d  (la archivada tiene %d)' % (
        t.default_code, n_rel, n_cfg, ref))
print('=' * 72)
