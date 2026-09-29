# -*- coding: utf-8 -*-
"""Revertir la copia de SPHMT03-05: salio con 207 especificaciones por producto
en vez de 10/11/10.

Causa: rv.copy() del rel arrastro su one2many de especificaciones, y ese
one2many no esta acotado al rel. Antes de la corrida las tres plantillas
tenian CERO de todo, asi que todo lo que cuelga de ellas lo creo el script y
se puede quitar entero sin tocar nada anterior.
"""
mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)
REL = env['amunet.quality.parameter.product.rel']
CFG = env['amunet.quality.parameter.specification.config']
NUEVOS = [2377, 2378, 2379]

rels = REL.with_context(active_test=False).search([('product_tmpl_id', 'in', NUEVOS)])
cfgs = CFG.search([('product_parameter_rel_id', 'in', rels.ids)])
# Nada de esto puede estar en uso: las plantillas se crearon el 23-sep vacias.
usados = env['amunet.quality.test.line.detail'].search_count([
    ('specification_config_id', 'in', cfgs.ids)])
assert usados == 0, 'Hay %d usos: NO se borra nada' % usados
ajenos = [c.id for c in cfgs if c.create_uid.id != mery.id]
assert not ajenos, 'Hay registros que no creo esta corrida: %s' % ajenos[:5]

print('borrando %d especificaciones y %d parametros' % (len(cfgs), len(rels)))
cfgs.unlink()
rels.unlink()
env.cr.commit()

for t in NUEVOS:
    print('  tmpl %s: rels=%d cfgs=%d' % (
        t, REL.search_count([('product_tmpl_id', '=', t)]),
        CFG.search_count([('product_parameter_rel_id.product_tmpl_id', '=', t)])))
