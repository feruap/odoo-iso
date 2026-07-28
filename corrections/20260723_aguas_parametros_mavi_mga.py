"""
Actualiza los códigos de parámetros de las 3 aguas (MPABI01, MPADE01, MPATR01):
  VAMA-004  → MAVI-13  (Bloqueo de la luz por partículas)
  VAMA-068  → MGA-0196 (Conductividad)
  VAMA-069  → MGA-0571 (Límites microbianos)
  VAMA-057  → MAVI-17  (Determinación de volumen — STBTR02)

También actualiza spec_configs y test_lines existentes con los nuevos códigos.
Límites microbianos usa campo de texto libre (text_pattern sin patrón).
Script idempotente: seguro de correr en cualquier estado de la base de datos.

Correr UNA VEZ después del deploy a producción.
"""
env = env  # noqa: F821 — Odoo shell

Param    = env['amunet.quality.check.parameter']
ParamRel = env['amunet.quality.parameter.product.rel']
SpecCfg  = env['amunet.quality.parameter.specification.config']
Product  = env['product.product']
TestLine = env['amunet.quality.test.line']

# ── 1. Tabla maestra de parámetros ───────────────────────────────────────────

updates_master = [
    ('VAMA-004', 'MAVI-13',  'Bloqueo de la luz por partículas'),
    ('VAMA-068', 'MGA-0196', 'Conductividad'),
    ('VAMA-069', 'MGA-0571', 'Límites microbianos'),
    ('VAMA-057', 'MAVI-17',  'Determinación de volumen'),
]
for old_code, new_code, new_name in updates_master:
    # idempotente: si ya tiene el nuevo código, no hace nada
    rec = Param.search([('code', '=', old_code)], limit=1)
    if rec:
        rec.write({'code': new_code, 'name': new_name})
        print(f"Maestro: {old_code} → {new_code}")
    else:
        already = Param.search([('code', '=', new_code)], limit=1)
        if already:
            print(f"Maestro: {new_code} ya existe, OK")
        else:
            print(f"AVISO: parámetro {old_code} / {new_code} no encontrado")

# ── 2. Relaciones producto-parámetro ─────────────────────────────────────────

for new_code, new_name in [
    ('MAVI-13',  'Bloqueo de la luz por partículas'),
    ('MGA-0196', 'Conductividad'),
    ('MGA-0571', 'Límites microbianos'),
    ('MAVI-17',  'Determinación de volumen'),
]:
    param = Param.search([('code', '=', new_code)], limit=1)
    if param:
        rels = ParamRel.search([('parameter_id', '=', param.id)])
        rels.write({'parameter_code': new_code, 'parameter_name': new_name})
        print(f"product_rel {new_code}: {len(rels)} actualizados")

# ── 3. Spec configs de las 3 aguas ───────────────────────────────────────────
# Límites microbianos → text_pattern (campo abierto, sin spec D.O. separada)
# Conductividad       → numeric_range con límite por tipo de agua
# pH                  → numeric_range 5.0–8.0

aguas = {
    'MPABI01': {'cond_max': 3.0, 'cond_text': '≤3 µs/cm'},
    'MPADE01': {'cond_max': 4.0, 'cond_text': '≤4 µs/cm'},
    'MPATR01': {'cond_max': 1.5, 'cond_text': '≤1.5 µs/cm'},
}

for code, cfg in aguas.items():
    product = Product.search([('default_code', '=', code), ('active', '=', True)], limit=1)
    if not product:
        print(f"AVISO: producto {code} no encontrado")
        continue
    rels_agua = ParamRel.search([('product_tmpl_id', '=', product.product_tmpl_id.id)])

    for rel in rels_agua:
        param_code = rel.parameter_id.code

        if param_code == 'MGA 0701':
            specs = SpecCfg.search([('product_parameter_rel_id', '=', rel.id)])
            specs.write({'min_value': 5.0, 'max_value': 8.0,
                         'acceptance_criteria': '5.0 – 8.0',
                         'specification_name': 'pH',
                         'evaluation_type': 'numeric_range'})
            print(f"{code} pH: {len(specs)} spec(s) → 5.0–8.0")

        elif param_code == 'MGA-0196':
            specs = SpecCfg.search([('product_parameter_rel_id', '=', rel.id)])
            specs.write({'min_value': 0.0, 'max_value': cfg['cond_max'],
                         'acceptance_criteria': cfg['cond_text'],
                         'specification_name': 'Conductividad',
                         'evaluation_type': 'numeric_range'})
            print(f"{code} Conductividad: {len(specs)} spec(s) → {cfg['cond_text']}")

        elif param_code == 'MGA-0571':
            # Un solo campo de texto libre — sin D.O. separado
            specs = SpecCfg.search([('product_parameter_rel_id', '=', rel.id)])
            specs.write({'evaluation_type': 'text_pattern',
                         'specification_name': 'Límites microbianos',
                         'acceptance_criteria': '≤100 UFC/10 mL o D.O. ≤0.6',
                         'min_value': None,
                         'max_value': None,
                         'text_pattern_expected': None,
                         'text_pattern_regex': None})
            print(f"{code} Límites microbianos: {len(specs)} spec(s) → text_pattern")

# ── 4. Checks existentes: actualizar código en amunet_quality_test_line ──────

for old_code, new_code, new_name in [
    ('VAMA-004', 'MAVI-13',  'Bloqueo de la luz por partículas'),
    ('VAMA-068', 'MGA-0196', 'Conductividad'),
    ('VAMA-069', 'MGA-0571', 'Límites microbianos'),
    ('VAMA-057', 'MAVI-17',  'Determinación de volumen'),
]:
    lines = TestLine.search([('code', '=', old_code)])
    if lines:
        lines.write({'code': new_code, 'name': new_name})
        print(f"test_line {old_code} → {new_code}: {len(lines)} línea(s)")

# ── 5. test_line_detail de Límites microbianos → text_pattern ────────────────
# Actualiza los detalles existentes para que usen el campo de texto libre.

env.cr.execute("""
    UPDATE amunet_quality_test_line_detail tld
    SET evaluation_type        = 'text_pattern',
        name                   = 'Límites microbianos',
        acceptance_criteria    = '≤100 UFC/10 mL o D.O. ≤0.6',
        min_value              = NULL,
        max_value              = NULL,
        text_pattern_expected  = NULL,
        text_pattern_regex     = NULL,
        write_date             = NOW()
    FROM amunet_quality_test_line tl
    JOIN product_product pp ON pp.id = tl.product_id
    WHERE tld.test_line_id = tl.id
      AND pp.default_code IN ('MPABI01','MPADE01','MPATR01')
      AND tl.code = 'MGA-0571'
""")
print(f"test_line_detail MGA-0571 aguas → text_pattern: {env.cr.rowcount} fila(s)")

env.cr.commit()
print("LISTO — parámetros de aguas actualizados.")
