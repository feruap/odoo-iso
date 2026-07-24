"""
Actualiza los códigos de parámetros de las 3 aguas (MPABI01, MPADE01, MPATR01):
  VAMA-004  → MAVI-13  (Bloqueo de la luz por partículas)
  VAMA-068  → MGA-0196 (Conductividad)
  VAMA-069  → MGA-0571 (Límites microbianos)
  VAMA-057  → MAVI-17  (Determinación de volumen — STBTR02)

También actualiza los criterios de aceptación y rangos de spec_config,
agrega la spec D.O. (≤0.6) para Límites microbianos de cada agua,
y corrige la tabla maestra amunet_quality_check_parameter para que los
checks existentes muestren los códigos actualizados.

Correr UNA VEZ después del deploy a producción.
"""
env = env  # noqa: F821 — Odoo shell

Param   = env['amunet.quality.check.parameter']
ParamRel = env['amunet.quality.parameter.product.rel']
SpecCfg  = env['amunet.quality.parameter.specification.config']
Product  = env['product.product']

# ── 1. Tabla maestra de parámetros ───────────────────────────────────────────

updates_master = [
    ('VAMA-004', 'MAVI-13',  'Bloqueo de la luz por partículas'),
    ('VAMA-068', 'MGA-0196', 'Conductividad'),
    ('VAMA-069', 'MGA-0571', 'Límites microbianos'),
    ('VAMA-057', 'MAVI-17',  'Determinación de volumen'),
]
for old_code, new_code, new_name in updates_master:
    rec = Param.search([('code', '=', old_code)], limit=1)
    if rec:
        rec.write({'code': new_code, 'name': new_name})
        print(f"Maestro: {old_code} → {new_code} ({new_name})")
    else:
        print(f"AVISO: parámetro maestro {old_code} no encontrado")

# ── 2. Relaciones producto-parámetro (parameter_code en amunet_quality_parameter_product_rel) ──

# MAVI-13 (antes VAMA-004) — aplica a todos los productos que lo usen
param_mavi13 = Param.search([('code', '=', 'MAVI-13')], limit=1)
if param_mavi13:
    rels = ParamRel.search([('parameter_id', '=', param_mavi13.id)])
    rels.write({'parameter_code': 'MAVI-13',
                'parameter_name': 'Bloqueo de la luz por partículas'})
    print(f"parameter_product_rel MAVI-13: {len(rels)} registros actualizados")

# MGA-0196 (antes VAMA-068) — Conductividad
param_mga196 = Param.search([('code', '=', 'MGA-0196')], limit=1)
if param_mga196:
    rels = ParamRel.search([('parameter_id', '=', param_mga196.id)])
    rels.write({'parameter_code': 'MGA-0196', 'parameter_name': 'Conductividad'})
    print(f"parameter_product_rel MGA-0196: {len(rels)} registros actualizados")

# MGA-0571 (antes VAMA-069) — Límites microbianos
param_mga571 = Param.search([('code', '=', 'MGA-0571')], limit=1)
if param_mga571:
    rels = ParamRel.search([('parameter_id', '=', param_mga571.id)])
    rels.write({'parameter_code': 'MGA-0571', 'parameter_name': 'Límites microbianos'})
    print(f"parameter_product_rel MGA-0571: {len(rels)} registros actualizados")

# MAVI-17 (antes VAMA-057) — Determinación de volumen
param_mavi17 = Param.search([('code', '=', 'MAVI-17')], limit=1)
if param_mavi17:
    rels = ParamRel.search([('parameter_id', '=', param_mavi17.id)])
    rels.write({'parameter_code': 'MAVI-17', 'parameter_name': 'Determinación de volumen'})
    print(f"parameter_product_rel MAVI-17: {len(rels)} registros actualizados")

# ── 3. Spec configs de las 3 aguas ───────────────────────────────────────────

aguas = {
    'MPABI01': {'conductividad_max': 3.0,  'conductividad_text': '≤3 µs/cm'},
    'MPADE01': {'conductividad_max': 4.0,  'conductividad_text': '≤4 µs/cm'},
    'MPATR01': {'conductividad_max': 1.5,  'conductividad_text': '≤1.5 µs/cm'},
}

for code, cfg in aguas.items():
    product = Product.search([('default_code', '=', code), ('active', '=', True)], limit=1)
    if not product:
        print(f"AVISO: producto {code} no encontrado")
        continue
    tmpl = product.product_tmpl_id
    rels_agua = ParamRel.search([('product_tmpl_id', '=', tmpl.id)])

    for rel in rels_agua:
        # pH: 5.0–8.0 para las 3 aguas
        if rel.parameter_id.code == 'MGA 0701':
            specs_ph = SpecCfg.search([('product_parameter_rel_id', '=', rel.id)])
            specs_ph.write({'min_value': 5.0, 'max_value': 8.0,
                            'acceptance_criteria': '5.0 – 8.0',
                            'specification_name': 'pH'})
            print(f"{code} pH: {len(specs_ph)} spec(s) → 5.0–8.0")

        # Conductividad: valor específico por agua
        elif rel.parameter_id.code == 'MGA-0196':
            specs_cond = SpecCfg.search([('product_parameter_rel_id', '=', rel.id)])
            specs_cond.write({'min_value': 0.0,
                              'max_value': cfg['conductividad_max'],
                              'acceptance_criteria': cfg['conductividad_text'],
                              'specification_name': 'Conductividad'})
            print(f"{code} Conductividad: {len(specs_cond)} spec(s) → {cfg['conductividad_text']}")

        # Límites microbianos: 0–100 UFC/10 mL + agregar D.O. si no existe
        elif rel.parameter_id.code == 'MGA-0571':
            # Actualizar spec UFC existente
            specs_ufc = SpecCfg.search([
                ('product_parameter_rel_id', '=', rel.id),
                ('specification_name', '=', 'Límites microbianos'),
            ])
            specs_ufc.write({'min_value': 0, 'max_value': 100,
                             'acceptance_criteria': '≤100 UFC/10 mL o D.O. ≤ 0.6',
                             'specification_name': 'Límites microbianos'})
            print(f"{code} Límites microbianos UFC: {len(specs_ufc)} spec(s)")

            # Crear spec D.O. si no existe
            existing_do = SpecCfg.search([
                ('product_parameter_rel_id', '=', rel.id),
                ('specification_name', '=', 'D.O. (Densidad óptica)'),
            ])
            if not existing_do:
                spec_id = SpecCfg.search([('product_parameter_rel_id', '=', rel.id)], limit=1).specification_id.id
                SpecCfg.create({
                    'product_parameter_rel_id': rel.id,
                    'specification_id': spec_id or 111,
                    'specification_name': 'D.O. (Densidad óptica)',
                    'evaluation_type': 'numeric_range',
                    'min_value': 0,
                    'max_value': 0.6,
                    'acceptance_criteria': '≤0.6',
                    'sequence': 20,
                })
                print(f"{code} D.O.: spec creada")

# ── 4. Checks existentes: actualizar código en amunet_quality_test_line ──────
# Las líneas guardan el código de forma denormalizada; hay que actualizarlas
# para que los análisis ya creados muestren los nuevos códigos.

codigos = [
    ('VAMA-004', 'MAVI-13',  'Bloqueo de la luz por partículas'),
    ('VAMA-068', 'MGA-0196', 'Conductividad'),
    ('VAMA-069', 'MGA-0571', 'Límites microbianos'),
    ('VAMA-057', 'MAVI-17',  'Determinación de volumen'),
]
TestLine = env['amunet.quality.test.line']
for old_code, new_code, new_name in codigos:
    lines = TestLine.search([('code', '=', old_code)])
    if lines:
        lines.write({'code': new_code, 'name': new_name})
        print(f"test_line {old_code} → {new_code}: {len(lines)} línea(s)")

# ── 5. Checks existentes: agregar test_line_detail D.O. si falta ─────────────
# Los checks de aguas ya existentes en la DB no tienen el detalle de D.O.
# porque se crearon antes de este fix.

TestLineDetail = env['amunet.quality.test.line.detail']
for code in ('MPABI01', 'MPADE01', 'MPATR01'):
    product = Product.search([('default_code', '=', code), ('active', '=', True)], limit=1)
    if not product:
        continue
    # Buscar checks de este producto
    tls = TestLine.search([('product_id', '=', product.id), ('code', '=', 'MGA-0571')])
    for tl in tls:
        existing = TestLineDetail.search([
            ('test_line_id', '=', tl.id),
            ('name', '=', 'D.O. (Densidad óptica)'),
        ])
        if not existing:
            # Buscar spec_config D.O. para este rel
            sc_do = SpecCfg.search([
                ('product_parameter_rel_id', 'in', tl.product_parameter_rel_ids.ids if hasattr(tl, 'product_parameter_rel_ids') else []),
                ('specification_name', '=', 'D.O. (Densidad óptica)'),
            ], limit=1)
            TestLineDetail.create({
                'test_line_id': tl.id,
                'check_id': tl.check_id.id,
                'specification_config_id': sc_do.id if sc_do else False,
                'specification_id': 111,
                'name': 'D.O. (Densidad óptica)',
                'evaluation_type': 'numeric_range',
                'min_value': 0,
                'max_value': 0.6,
                'acceptance_criteria': '≤0.6',
                'sequence': 20,
            })
            print(f"{code} check {tl.check_id.id}: tld D.O. creado")

env.cr.commit()
print("LISTO — parámetros de aguas, specs D.O. y checks existentes actualizados.")
