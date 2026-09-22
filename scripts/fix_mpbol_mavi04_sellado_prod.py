"""
CORRECCIÓN MPBOL01-05 en PRODUCCIÓN (amunet_prod)
==================================================
Cambios:
  1. Agrega spec "Sellado" (id=190, binary_selection) al bloque MAVI-04
     de las 5 bolsas termosellables si no existe aún.

  2. Desactiva los spec configs de VAMA-091 (cfg_ids 71337,71345,71353,71361,71369).

  3. Desactiva los bloques producto-parámetro de VAMA-091
     (rel_ids 516,518,520,521,522).

Resultado: cada bolsa queda con MAVI-04 = Polvo + Manchas + Rasgaduras
           + Deformidad + Sellado.  VAMA-091 desaparece del análisis.

IDs verificados contra producción 2026-09-22.
Solicitado por: Diana Flores — Control de Calidad, 2026-09-22
"""

Config = env['amunet.quality.parameter.specification.config']
Rel    = env['amunet.quality.parameter.product.rel']

# MAVI-04 rel_ids de las 5 bolsas (Aspectos, param_id=1)
MAVI04_REL_IDS = {
    'MPBOL01': 133,
    'MPBOL02': 134,
    'MPBOL03': 136,
    'MPBOL04': 138,
    'MPBOL05': 139,
}
SPEC_SELLADO     = 190   # "Sellado" binary_selection, MAVI-04
PARAM_MAVI04     = 1     # "Aspectos" MAVI-04

# VAMA-091 cfg_ids (los spec configs activos)
VAMA091_CFG_IDS  = [71337, 71345, 71353, 71361, 71369]
# VAMA-091 rel_ids (los bloques producto-parámetro)
VAMA091_REL_IDS  = [516, 518, 520, 521, 522]

# ── PASO 1: Agregar Sellado a MAVI-04 si no existe ──────────────────────────
print("--- PASO 1: Agregar Sellado a MAVI-04 ---")
for code, rel_id in MAVI04_REL_IDS.items():
    rel = Rel.browse(rel_id)
    pt  = rel.product_tmpl_id
    ya_tiene = Config.search([
        ('product_parameter_rel_id', '=', rel_id),
        ('specification_id', '=', SPEC_SELLADO),
        ('active', '=', True),
    ], limit=1)
    if ya_tiene:
        print(f"  {code}: Sellado ya existe (cfg={ya_tiene.id}), sin cambio")
    else:
        cfg = Config.create({
            'product_parameter_rel_id': rel_id,
            'specification_id': SPEC_SELLADO,
            'product_tmpl_id': pt.id,
            'parameter_id': PARAM_MAVI04,
            'evaluation_type': 'binary_selection',
            'sequence': 50,
            'acceptance_criteria': 'Sellado adecuado sin defectos visibles',
            'active': True,
        })
        print(f"  {code}: Sellado agregado (cfg={cfg.id})")

# ── PASO 2: Desactivar specs de VAMA-091 ────────────────────────────────────
print("\n--- PASO 2: Desactivar spec configs VAMA-091 ---")
vama_cfgs = Config.browse(VAMA091_CFG_IDS).filtered(lambda c: c.active)
print(f"  Desactivando {len(vama_cfgs)} configs: {vama_cfgs.ids}")
vama_cfgs.write({'active': False})

# ── PASO 3: Desactivar bloques producto-parámetro VAMA-091 ──────────────────
print("\n--- PASO 3: Desactivar rels VAMA-091 ---")
vama_rels = Rel.browse(VAMA091_REL_IDS).filtered(lambda r: r.active)
print(f"  Desactivando {len(vama_rels)} rels: {vama_rels.ids}")
vama_rels.write({'active': False})

env.cr.commit()
print("\n✓ Cambios guardados en producción.")
print("Resultado: MPBOL01-05 tienen MAVI-04 con Polvo, Manchas, Rasgaduras, Deformidad, Sellado.")
print("           VAMA-091 desactivado en las 5 bolsas.")
