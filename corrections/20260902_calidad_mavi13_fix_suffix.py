"""Fix: binary_suffix duplicaba texto en SpecConf de MAVI-13."""
SpecConf = env['amunet.quality.parameter.specification.config']

PASS = 'Sin partículas suspendidas'
FAIL = 'Con partículas suspendidas'

for sc_id in [88923, 88940, 88957]:
    sc = SpecConf.with_context(active_test=False).browse(sc_id)
    if sc.exists():
        sc.write({
            'binary_prefix':          f'{PASS}/{FAIL}',
            'binary_suffix':          '',
            'binary_expected_option': 'with_prefix',
        })
        print(f"  SpecConf {sc_id}: pass='{sc.binary_option_pass}' fail='{sc.binary_option_fail}'")

env.cr.commit()
print("✓ Listo.")
