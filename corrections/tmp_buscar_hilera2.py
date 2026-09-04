"""
Buscar por variaciones del nombre: hilera, caja, rack, gradilla, soporte.
También buscar quién tiene MAVI-11 y VAMA-023.
"""
import json

ProdTmpl = env['product.template']
Param    = env['amunet.quality.check.parameter']
Rel      = env['amunet.quality.parameter.product.rel']
SpecConf = env['amunet.quality.parameter.specification.config']
QPoint   = env['amunet.quality.point']

param_mavi11  = Param.browse(64)
param_vama023 = Param.browse(72)

# Buscar todos los productos que tienen MAVI-11 Y VAMA-023
rels_mavi11  = Rel.with_context(active_test=False).search([('parameter_id', '=', 64)])
rels_vama023 = Rel.with_context(active_test=False).search([('parameter_id', '=', 72)])

tmpl_mavi11  = set(rels_mavi11.mapped('product_tmpl_id.id'))
tmpl_vama023 = set(rels_vama023.mapped('product_tmpl_id.id'))
ambos = tmpl_mavi11 & tmpl_vama023

print(f"Productos con MAVI-11: {len(tmpl_mavi11)}")
print(f"Productos con VAMA-023: {len(tmpl_vama023)}")
print(f"Productos con AMBOS: {len(ambos)}")
print()

# Ver los que tienen ambos
for tmpl_id in sorted(ambos):
    t = ProdTmpl.with_context(active_test=False).browse(tmpl_id)
    print(f"  id={tmpl_id} '{t.default_code}' '{t.name}'")

# Ver todos los que tienen MAVI-11 (no solo los que tienen ambos)
print(f"\nTodos con MAVI-11:")
for r in rels_mavi11:
    t = r.product_tmpl_id
    specs = SpecConf.with_context(active_test=False).search([
        ('product_parameter_rel_id', '=', r.id),
        ('active', '=', True),
    ])
    for s in specs:
        crit = s.acceptance_criteria or ''
        if '15' in crit or 'cm' in crit.lower() or 'mm' in crit.lower():
            print(f"  '{t.default_code}' '{t.name}' | spec: {s.specification_id.name if s.specification_id else '-'} | criterio: {crit[:80]}")
