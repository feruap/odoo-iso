"""
Mejora evaluación de Límites microbianos (MGA-0571) en las 3 aguas:
  MPABI01 (bidestilada), MPADE01 (destilada), MPATR01 (tridestilada)

  - Cambia a conditional_numeric_range para que el analista elija el método
    con el que midió y el sistema valide automáticamente:
      • UFC/10 mL  → acepta si valor ≤ 100
      • D.O. 620nm → acepta si valor ≤ 0.6

También corrige cualquier tld de conductividad (MGA-0196) de las 3 aguas
que haya quedado con evaluation_type = binary_selection (debe ser numeric_range).

Idempotente y sin IDs hardcodeados — seguro en staging y producción.
Correr UNA VEZ después del deploy.
"""
env = env  # noqa: F821 — Odoo shell

MasterSpec = env['amunet.quality.check.parameter.specification']
SpecCfg    = env['amunet.quality.parameter.specification.config']
ConditOpt  = env['amunet.quality.parameter.conditional.option']
Param      = env['amunet.quality.check.parameter']
ParamRel   = env['amunet.quality.parameter.product.rel']
Product    = env['product.product']

AGUAS = ('MPABI01', 'MPADE01', 'MPATR01')

# ── 1. Spec maestra de "Agentes biológicos / Límites microbianos" ─────────────
# Buscar por nombre; si hay varias, tomar la que esté ligada al param MGA-0571.
param_mga = Param.search([('code', '=', 'MGA-0571')], limit=1)
if not param_mga:
    print("AVISO: parámetro MGA-0571 no encontrado — verifica que el script de códigos ya corrió")
    raise SystemExit(1)

# Spec maestra: la que esté en uso en los spec_configs de las aguas
agua_products = Product.search([('default_code', 'in', list(AGUAS)), ('active', '=', True)])
agua_tmpl_ids = agua_products.mapped('product_tmpl_id').ids
rels_agua = ParamRel.search([
    ('product_tmpl_id', 'in', agua_tmpl_ids),
    ('parameter_id', '=', param_mga.id),
])
if not rels_agua:
    print("AVISO: no se encontraron relaciones producto-parámetro para MGA-0571 en las aguas")
    raise SystemExit(1)

# Obtener spec_configs de MGA-0571 para las 3 aguas
agua_spec_configs = SpecCfg.search([
    ('product_parameter_rel_id', 'in', rels_agua.ids),
])

# La spec maestra puede venir de cualquiera de ellos (todas usan la misma)
spec = agua_spec_configs[0].specification_id if agua_spec_configs else None
if not spec:
    print("AVISO: no hay spec_configs para MGA-0571 en las aguas")
    raise SystemExit(1)

print(f"Spec maestra: id={spec.id} '{spec.name}' eval_type={spec.evaluation_type}")

if spec.evaluation_type != 'conditional_numeric_range':
    spec.write({'evaluation_type': 'conditional_numeric_range'})
    print("  → cambiado a conditional_numeric_range")
else:
    print("  → ya es conditional_numeric_range, OK")

# ── 2. Opciones condicionales ─────────────────────────────────────────────────
opciones = [
    {'name': 'UFC/10 mL',  'min_value': 0.0, 'max_value': 100.0, 'sequence': 10},
    {'name': 'D.O. 620nm', 'min_value': 0.0, 'max_value': 0.6,   'sequence': 20},
]
opt_ids = []
for od in opciones:
    opt = ConditOpt.search([
        ('specification_id', '=', spec.id),
        ('name', '=', od['name']),
    ], limit=1)
    if opt:
        opt.write({'min_value': od['min_value'], 'max_value': od['max_value'], 'active': True})
        print(f"  Opción '{od['name']}' id={opt.id}: rangos confirmados")
    else:
        opt = ConditOpt.create({
            'specification_id': spec.id,
            'name': od['name'],
            'min_value': od['min_value'],
            'max_value': od['max_value'],
            'sequence': od['sequence'],
            'active': True,
        })
        print(f"  Opción '{od['name']}' creada id={opt.id}")
    opt_ids.append(opt.id)

# ── 3. Vincular opciones a los spec_configs de las 3 aguas ───────────────────
for sc in agua_spec_configs:
    existing = sc.active_conditional_option_ids.ids
    missing = [oid for oid in opt_ids if oid not in existing]
    if missing:
        sc.write({'active_conditional_option_ids': [(4, oid) for oid in missing]})
    # Actualizar stored evaluation_type en la columna (related almacenado)
    env.cr.execute(
        "UPDATE amunet_quality_parameter_specification_config "
        "SET evaluation_type='conditional_numeric_range', write_date=NOW() WHERE id=%s",
        (sc.id,)
    )
    print(f"  SpecConfig {sc.id} ({sc.specification_name}): opciones y tipo actualizados")

# ── 4. Actualizar test_line_detail existentes de MGA-0571 en las 3 aguas ─────
env.cr.execute("""
    UPDATE amunet_quality_test_line_detail tld
    SET evaluation_type     = 'conditional_numeric_range',
        result_binary_option = NULL,
        result_notes        = NULL,
        min_value           = NULL,
        max_value           = NULL,
        acceptance_criteria = '≤100 UFC/10 mL o D.O. ≤0.6',
        name                = 'Límites microbianos',
        write_date          = NOW()
    FROM amunet_quality_test_line tl
    JOIN amunet_quality_check qc ON qc.id = tl.check_id
    JOIN product_product pp ON pp.id = qc.product_id
    WHERE tld.test_line_id = tl.id
      AND pp.default_code IN ('MPABI01','MPADE01','MPATR01')
      AND tl.code = 'MGA-0571'
""")
print(f"test_line_detail MGA-0571: {env.cr.rowcount} tld(s) → conditional_numeric_range")

# ── 5. Corregir conductividad (MGA-0196) con binary_selection en las 3 aguas ──
env.cr.execute("""
    UPDATE amunet_quality_test_line_detail tld
    SET evaluation_type = 'numeric_range',
        write_date      = NOW()
    FROM amunet_quality_test_line tl
    JOIN amunet_quality_check qc ON qc.id = tl.check_id
    JOIN product_product pp ON pp.id = qc.product_id
    WHERE tld.test_line_id = tl.id
      AND pp.default_code IN ('MPABI01','MPADE01','MPATR01')
      AND tl.code = 'MGA-0196'
      AND tld.evaluation_type = 'binary_selection'
""")
print(f"Conductividad binary_selection corregida: {env.cr.rowcount} tld(s) → numeric_range")

env.cr.commit()
print("LISTO — Límites microbianos: analista elige método y el sistema valida automáticamente.")
