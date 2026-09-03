"""
Fix: MAVI-13 opciones binary_selection vacías en controles negativos.

Problema: el SpecConf de MAVI-13 quedó sin binary_prefix, por lo que
binary_option_pass/fail están en blanco y el widget no muestra opciones.

Corrección:
  - SpecConf de STCNL01/STCON01/SPCNL04: binary_prefix = "Sin partículas/Con partículas"
  - Detail 7584 (análisis 785): binary_option_pass/fail directos

Idempotente. Confirmado por Diana Flores, 2026-09-02.
"""

SpecConf = env['amunet.quality.parameter.specification.config']
Detail   = env['amunet.quality.test.line.detail']
Param    = env['amunet.quality.check.parameter']
Rel      = env['amunet.quality.parameter.product.rel']
ProdTmpl = env['product.template']

CONTROLES = ['STCNL01', 'STCON01', 'SPCNL04']
param_mavi13 = Param.browse(71)

OPCION_PASS = 'Sin partículas suspendidas'
OPCION_FAIL = 'Con partículas suspendidas'

print("── Actualizando SpecConf de MAVI-13 en controles negativos ──")
for codigo in CONTROLES:
    tmpl = ProdTmpl.search([('default_code', '=', codigo)], limit=1)
    if not tmpl:
        print(f"  {codigo}: no encontrado")
        continue
    rel = Rel.search([
        ('product_tmpl_id', '=', tmpl.id),
        ('parameter_id',    '=', param_mavi13.id),
    ], limit=1)
    if not rel:
        print(f"  {codigo}: sin rel MAVI-13")
        continue
    sc = SpecConf.with_context(active_test=False).search([
        ('product_parameter_rel_id', '=', rel.id),
    ], limit=1)
    if sc:
        sc.write({
            'binary_prefix': f'{OPCION_PASS}/{OPCION_FAIL}',
            'binary_expected_option': 'with_prefix',
        })
        print(f"  {codigo}: SpecConf id={sc.id} → pass='{sc.binary_option_pass}' fail='{sc.binary_option_fail}'")
    else:
        print(f"  {codigo}: sin SpecConf")

print("\n── Actualizando detail 7584 (análisis 785) ──")
detail = Detail.browse(7584)
if detail.exists():
    detail.write({
        'binary_option_pass': OPCION_PASS,
        'binary_option_fail': OPCION_FAIL,
    })
    print(f"  Detail 7584: pass='{detail.binary_option_pass}' fail='{detail.binary_option_fail}'")
else:
    print(f"  Detail 7584 no encontrado")

env.cr.commit()
print("\n✓ Opciones MAVI-13 corregidas.")
