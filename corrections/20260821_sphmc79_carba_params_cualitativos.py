"""
Configura los parámetros de control de calidad para SPHMC79 (Hoja Maestra CARBA 5en1)
con estructura cualitativa igual a SPHMC77 (referencia aprobada):

  MAVI-04 × 3  — Rasgaduras | Manchas y/o suciedad | Deformidad o deterioro
  MAVI-07 × 2  — Muestra positiva (vama_multi_check) | Muestra negativa
  MAVI-09 × 2  — Tiempo de liberación (1–30 s) | Tiempo de migración (30–180 s)
  MAVI-11 × 1  — Altura 6 u 8 cm (conditional_numeric_range)

Idempotente: elimina configs viejas y recrea las 8 correctas.
Correr en producción una sola vez tras el deploy.

Autorizado por: Diana Flores (s.controldecalidad@amunet.com.mx)
Fecha: 2026-08-21
"""

Product  = env['product.product']
Param    = env['amunet.quality.check.parameter']
ParamRel = env['amunet.quality.parameter.product.rel']
SpecCfg  = env['amunet.quality.parameter.specification.config']

CODIGO = 'SPHMC79'

# IDs de parámetros maestros (verificados en staging)
PARAM_MAVI04 = 1
PARAM_MAVI07 = 65
PARAM_MAVI09 = 69
PARAM_MAVI11 = 64

product = Product.search([('default_code', '=', CODIGO), ('active', '=', True)], limit=1)
if not product:
    print(f"ERROR: producto {CODIGO} no encontrado")
    raise SystemExit(1)

tmpl_id = product.product_tmpl_id.id
print(f"\n{CODIGO} — tmpl_id={tmpl_id}")

# ── Paso 1: Asegurar ParamRels ────────────────────────────────────────────────
rels = {}
for param_id in [PARAM_MAVI04, PARAM_MAVI07, PARAM_MAVI09, PARAM_MAVI11]:
    param = Param.browse(param_id)
    rel = ParamRel.search([
        ('product_tmpl_id', '=', tmpl_id),
        ('parameter_id', '=', param_id),
    ], limit=1)
    if not rel:
        rel = ParamRel.create({
            'product_tmpl_id': tmpl_id,
            'parameter_id':    param_id,
            'parameter_code':  param.code,
            'parameter_name':  param.name,
        })
        print(f"  ParamRel creado: {param.code}")
    else:
        print(f"  ParamRel ya existe (id={rel.id}): {param.code}")
    rels[param_id] = rel.id

env.cr.commit()

# ── Paso 2: Limpiar todos los spec_configs existentes ────────────────────────
for param_id, rel_id in rels.items():
    env.cr.execute(
        "DELETE FROM amunet_quality_parameter_specification_config WHERE product_parameter_rel_id=%s",
        (rel_id,)
    )
    print(f"  {Param.browse(param_id).code}: {env.cr.rowcount} configs borrados")

# ── Paso 3: Crear los 8 configs correctos ────────────────────────────────────

rel04 = rels[PARAM_MAVI04]
rel07 = rels[PARAM_MAVI07]
rel09 = rels[PARAM_MAVI09]
rel11 = rels[PARAM_MAVI11]

# MAVI-04: 3 inspecciones visuales (igual a SPHMC77)
aspectos = [
    (170, 'Rasgaduras',          'Rasgaduras',          'Sin Rasgaduras',          'Con Rasgaduras'),
    (171, 'Manchas y/o suciedad','Manchas y/o suciedad', 'Sin Manchas y/o suciedad','Con Manchas y/o suciedad'),
    (204, 'Deformidad o deterioro.','Deformidad o deterioro.','Sin Deformidad o deterioro.','Con Deformidad o deterioro.'),
]
for seq, (spec_id, name, criteria, opt_pass, opt_fail) in enumerate(aspectos, start=1):
    env.cr.execute("""
        INSERT INTO amunet_quality_parameter_specification_config
          (product_parameter_rel_id, specification_id, specification_name,
           evaluation_type, acceptance_criteria,
           binary_option_pass, binary_option_fail,
           min_value, max_value, sequence,
           create_date, write_date, create_uid, write_uid)
        VALUES (%s, %s, %s, 'binary_selection', %s, %s, %s, 0, 0, %s, NOW(), NOW(), 1, 1)
    """, (rel04, spec_id, name, criteria, opt_pass, opt_fail, seq * 10))

# MAVI-07: positiva y negativa (vama_multi_check, igual a SPHMC77)
env.cr.execute("""
    INSERT INTO amunet_quality_parameter_specification_config
      (product_parameter_rel_id, specification_id, specification_name,
       evaluation_type, acceptance_criteria, sequence,
       create_date, write_date, create_uid, write_uid)
    VALUES
      (%s, 629, 'Muestra positiva', 'vama_multi_check',
       'Patrones #1-#4 (Línea T visible)', 1, NOW(), NOW(), 1, 1),
      (%s, 628, 'Muestra negativa', 'vama_multi_check',
       'Patrón #5 (Solo línea control, sin línea T)', 2, NOW(), NOW(), 1, 1)
""", (rel07, rel07))

# MAVI-09: liberación y migración con opciones binarias (igual a SPHMC77)
env.cr.execute("""
    INSERT INTO amunet_quality_parameter_specification_config
      (product_parameter_rel_id, specification_id, specification_name,
       evaluation_type, acceptance_criteria,
       binary_option_pass, binary_option_fail,
       min_value, max_value, sequence,
       create_date, write_date, create_uid, write_uid)
    VALUES
      (%s, 146, 'Tiempo de liberación', 'numeric_range',
       '1 a 30 segundos', 'Captura [    ] segundos', 'No captura [    ] segundos',
       1, 30, 10, NOW(), NOW(), 1, 1),
      (%s, 126, 'Tiempo de migración', 'numeric_range',
       '30 a 180 segundos', 'Captura [    ] segundos', 'No captura [    ] segundos',
       30, 180, 10, NOW(), NOW(), 1, 1)
""", (rel09, rel09))

# MAVI-11: altura condicional (igual a SPHMC77)
env.cr.execute("""
    INSERT INTO amunet_quality_parameter_specification_config
      (product_parameter_rel_id, specification_id, specification_name,
       evaluation_type, acceptance_criteria,
       binary_option_pass, binary_option_fail,
       min_value, max_value, sequence,
       create_date, write_date, create_uid, write_uid)
    VALUES (%s, 414, 'Altura 6 u 8 cm (según aplique)', 'conditional_numeric_range',
            'Altura 6 u 8 cm (según aplique)', 'Seleccione', 'Opción A: 6 cm.',
            0, 0, 10, NOW(), NOW(), 1, 1)
""", (rel11,))

env.cr.commit()
print(f"\n✅ SPHMC79 — 8 controles configurados correctamente (igual a SPHMC77).")
print("Verificar en producción: crear un análisis de QC para SPHMC79 y validar el formulario.")
