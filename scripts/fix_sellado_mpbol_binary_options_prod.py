"""
CORRECCIÓN: binary_option_pass/fail vacíos en spec "Sellado" de MPBOL01-05 (producción)
========================================================================================
Los 5 cfg_ids del spec "Sellado" agregados al MAVI-04 de bolsas no tenían opciones.

cfg_ids afectados: 90642 (MPBOL01), 90643 (MPBOL02), 90644 (MPBOL03),
                   90645 (MPBOL04), 90646 (MPBOL05)

Solicitado por: Diana Flores — Control de Calidad, 2026-09-23
"""

Config = env['amunet.quality.parameter.specification.config']

CFG_IDS = [90642, 90643, 90644, 90645, 90646]

cfgs = Config.browse(CFG_IDS).filtered(lambda c: c.active)
print(f"Configs encontradas: {len(cfgs)}")

for cfg in cfgs:
    pt_code = cfg.product_tmpl_id.default_code if cfg.product_tmpl_id else '?'
    cfg.write({
        'binary_option_pass': 'Sellado adecuado',
        'binary_option_fail': 'Sellado defectuoso',
    })
    print(f"  ✓ {pt_code} — cfg {cfg.id}: Sellado adecuado / Sellado defectuoso")

env.cr.commit()
print(f"\n✓ {len(cfgs)} specs de Sellado corregidas.")
