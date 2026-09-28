"""
CORRECCIÓN STGOT02 — Desactivar VAMA-038 duplicado (producción)
===============================================================
STGOT02 (Gotero de 5 µL) tiene VAMA-038 con 5 configs duplicadas
(4 con rangos en cero, 1 con 0-10). MAVI-17 "Conteo de gotas" (5-10)
ya cubre esa evaluación, por lo que VAMA-038 se desactiva.

Solicitado por: Diana Flores — Control de Calidad, 2026-09-25
"""

Rel = env['amunet.quality.parameter.product.rel']
Cfg = env['amunet.quality.parameter.specification.config']

# IDs confirmados en producción
cfg_ids = [73122, 90058, 90059, 90060, 90061]
rel_id  = 409

print("── Desactivando VAMA-038 en STGOT02 ──")
cfgs = Cfg.browse(cfg_ids)
for c in cfgs:
    print(f"  cfg {c.id}: '{c.specification_name.strip()}' ({c.min_value}-{c.max_value})")
cfgs.write({'active': False})

rel = Rel.browse(rel_id)
rel.write({'active': False})
print(f"  Rel {rel_id} desactivada.")

env.cr.commit()

# Verificación
print("\n── Verificación STGOT02 ──")
Prod = env['product.template']
tmpl = Prod.search([('default_code', '=', 'STGOT02')], limit=1)
rels_activas = Rel.search([('product_tmpl_id', '=', tmpl.id), ('active', '=', True)])
for r in rels_activas:
    cfgs_ok = Cfg.search([('product_parameter_rel_id', '=', r.id), ('active', '=', True)])
    for c in cfgs_ok:
        rango = f"{c.min_value}-{c.max_value}" if c.evaluation_type == 'numeric_range' else ''
        print(f"  {r.parameter_code}: {c.specification_name.strip()} {rango}")

print("\n✓ VAMA-038 eliminado. MAVI-17 (5-10 gotas) queda como único parámetro de volumen.")
