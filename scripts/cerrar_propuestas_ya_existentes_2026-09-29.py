# -*- coding: utf-8 -*-
"""Cerrar las propuestas de productos que YA existian en el catalogo.

POR QUE ESTABAN ABIERTAS. No fue descuido de quien las levanto: los 14
productos existen en Odoo -- con clave, proveedor, existencia y movimientos --
pero NO estaban publicados en el Marketplace. Quien los buscaba en el catalogo
no los encontraba, y lo unico que el sistema le ofrecia era proponerlos como
nuevos. Tris-HCl se propuso teniendo 7,999 g en el almacen.

Los 15 se publicaron el 29-sep, asi que estas propuestas ya no tienen objeto.

SE CIERRAN COMO 'CONVERTIDA', NO COMO 'RECHAZADA'. Rechazada dice "esto no se
compra", y no es el caso: el producto existe y ahora si se puede pedir.
Convertida con el producto ligado dice lo que de verdad paso, y deja a la
vista cual es la clave que hay que usar.

NO se cierran tres, porque siguen con duda y no la resuelvo yo:
  - Bata desechable AZUL: la que existe (COBDE01) no dice color.
  - Etanol: el que existe es al 96%; falta saber si sirve.
  - Biotina: no se sabe para que se pide; lo que hay es la hoja maestra y un
    anticuerpo anti-biotina, no el reactivo.

Idempotente. DRY_RUN=True no escribe.
"""
DRY_RUN = False

# nombre de la propuesta -> clave del producto que ya existia
PARES = [
    ('Triptona', 'MPREC94'),
    ('Peptona de Caseína', 'MPREC67'),
    ('DTT', 'MPREC26'),
    ('Inhibidor de proteasas', 'MPINP0101'),
    ('IPTG', 'MPREC25'),
    ('Tris-HCl', 'MPREC04'),
    ('Imidazol', 'MPREC53'),
    ('Sulfato de Magnesio', 'MPREC65'),
    ('EDTA', 'MPREC98'),
    ('Sulfato de amonio', 'MPREC41'),
    ('Ácido Acético', 'MPREC78'),
    ('NaCl', 'MPREC05'),
    ('KH2PO4', 'MPREC33'),
    ('NaOH', 'MPREC09'),
]

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)
PROP = env['amunet.marketplace.product.proposal']

cerradas, avisos = [], []
for nombre, clave in PARES:
    p = PROP.search([('name', '=', nombre)])
    if len(p) != 1:
        avisos.append((nombre, 'hay %d propuestas con ese nombre' % len(p))); continue
    if p.state in ('converted', 'rejected'):
        avisos.append((nombre, 'ya estaba %s' % p.state)); continue
    prod = env['product.product'].search([('default_code', '=', clave)], limit=1)
    if not prod:
        avisos.append((nombre, 'no existe %s' % clave)); continue
    t = prod.product_tmpl_id
    if not t.marketplace_enabled:
        avisos.append((nombre, '%s existe pero NO esta publicado: no se cierra' % clave)); continue
    if not DRY_RUN:
        p.with_context(marketplace_proposal_internal_write=True).write({
            'product_tmpl_id': t.id,
            'state': 'converted',
            'manager_notes': (
                'Cerrada el 29-sep-2026: el producto ya existia como %s "%s". '
                'No estaba publicado en el catalogo y por eso no se encontraba; '
                'ya quedo visible. Pidelo con esa clave.' % (clave, t.name)),
        })
        p.message_post(body=(
            'Propuesta cerrada: <b>%s</b> ya existe en el catalogo como <b>%s</b>, '
            'con %s de existencia. Se publico en el Marketplace el 29-sep-2026.'
        ) % (nombre, clave, sum(env['stock.quant'].search([
            ('product_id', '=', prod.id), ('location_id.usage', '=', 'internal')]).mapped('quantity'))))
    cerradas.append((nombre, clave, t.name))

if not DRY_RUN:
    env.cr.commit()

print('=' * 84)
print('SIMULACION — no se escribio nada' if DRY_RUN else 'APLICADO')
print('-' * 84)
for nombre, clave, real in cerradas:
    print('  %-24s -> %-10s %s' % (nombre[:24], clave, real[:36]))
print('  cerradas: %d' % len(cerradas))
if avisos:
    print('-' * 84)
    for n, m in avisos:
        print('  [!] %-24s %s' % (n[:24], m))
print('-' * 84)
for est, n in env.cr.execute("SELECT state, count(*) FROM amunet_marketplace_product_proposal GROUP BY 1 ORDER BY 2 DESC") or []:
    pass
env.cr.execute("SELECT state, count(*) FROM amunet_marketplace_product_proposal GROUP BY 1 ORDER BY 2 DESC")
for est, n in env.cr.fetchall():
    print('  propuestas %-12s %s' % (est, n))
print('=' * 84)
