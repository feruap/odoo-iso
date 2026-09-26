"""
MIGRACIÓN HISOPOS — MAVI-23 + LIMPIEZA MAVI-04 duplicado (staging)
====================================================================
1. Quitar bloque duplicado MAVI-04 (el de 3 specs) en STHIS01-06.
2. Agregar MAVI-23 "Funcionalidad prevista" a STHIS02-06 con specs y rangos correctos.
3. Desactivar VAMA-092, VAMA-093, VAMA-104 en los hisopos correspondientes.

Rangos de absorción corregidos:
  STHIS02: 120-160 µL → 130-150 µL
  STHIS03: 130-180 µL → 140-170 µL
  STHIS06: 130-180 µL → 140-170 µL

Solicitado por: Diana Flores — Control de Calidad, 2026-09-24
"""

Rel   = env['amunet.quality.parameter.product.rel']
Cfg   = env['amunet.quality.parameter.specification.config']
Spec  = env['amunet.quality.check.parameter.specification']
Param = env['amunet.quality.check.parameter']
Prod  = env['product.template']

# ─────────────────────────────────────────────────────────────────
# 1. Quitar bloque MAVI-04 duplicado (el de 3 specs — sin Rasgaduras)
# ─────────────────────────────────────────────────────────────────
rels_duplicado = [3133, 3135, 3137, 3139, 3141, 3143]
print("── 1. Desactivando bloque MAVI-04 duplicado ──")
for rel in Rel.browse(rels_duplicado):
    cfgs = Cfg.search([('product_parameter_rel_id', '=', rel.id)])
    print(f"  {rel.product_tmpl_id.default_code} rel {rel.id}: {len(cfgs)} configs")
    cfgs.write({'active': False})
    rel.write({'active': False})

# ─────────────────────────────────────────────────────────────────
# 2. Obtener parámetro MAVI-23 y sus specs
# ─────────────────────────────────────────────────────────────────
param_mavi23 = Param.search([('code', '=', 'MAVI-23')], limit=1)
if not param_mavi23:
    raise SystemExit("ERROR: MAVI-23 no existe. Ejecuta primero el update del módulo.")

specs_by_name = {s.name: s.id for s in Spec.search([('parameter_id', '=', param_mavi23.id)])}
print(f"\nMAVI-23 id {param_mavi23.id} — specs: {list(specs_by_name.keys())}")

# IDs de specs de MAVI-23
ID_ABSORCION  = specs_by_name.get('Absorción')
ID_EXPULSION  = specs_by_name.get('Expulsión de cabeza del cepillo por el tubo transparente.')
ID_EXTENSION  = specs_by_name.get('1. Prueba de extensión y retracción')
ID_FIRMEZA    = specs_by_name.get('2. Prueba de firmeza en posición')
ID_PRESION    = specs_by_name.get('3. Prueba de resistencia bajo presión')

# ─────────────────────────────────────────────────────────────────
# 3. Configuración por hisopo
# ─────────────────────────────────────────────────────────────────
# specs_activas: spec_id → dict con overrides de valores
# specs_desactivar: set de spec_ids a desactivar en la rel generada
HISOPOS = [
    {
        'codigo': 'STHIS02', 'rel_vama': 1339,
        'specs_activas': {
            ID_ABSORCION: {'min_value': 130.0, 'max_value': 150.0, 'acceptance_criteria': '130-150 µL'},
        },
        'specs_desactivar': {ID_EXPULSION, ID_EXTENSION, ID_FIRMEZA, ID_PRESION},
    },
    {
        'codigo': 'STHIS03', 'rel_vama': 1343,
        'specs_activas': {
            ID_ABSORCION: {'min_value': 140.0, 'max_value': 170.0, 'acceptance_criteria': '140-170 µL'},
        },
        'specs_desactivar': {ID_EXPULSION, ID_EXTENSION, ID_FIRMEZA, ID_PRESION},
    },
    {
        'codigo': 'STHIS04', 'rel_vama': 1347,
        'specs_activas': {
            ID_EXPULSION: {
                'binary_option_pass': 'La cabeza del cepillo es expulsada completamente por el tubo transparente.',
                'binary_option_fail': 'La cabeza del cepillo no es expulsada completamente por el tubo transparente.',
                'acceptance_criteria': 'La cabeza del cepillo es expulsada completamente por el tubo transparente.',
            },
        },
        'specs_desactivar': {ID_ABSORCION, ID_EXTENSION, ID_FIRMEZA, ID_PRESION},
    },
    {
        'codigo': 'STHIS05', 'rel_vama': 1351,
        'specs_activas': {
            ID_EXTENSION: {
                'binary_option_pass': 'Se extiende y retrae sin fallas.',
                'binary_option_fail': 'Presenta fallas al extender o retraer.',
                'acceptance_criteria': 'Se extiende y retrae sin fallas.',
            },
            ID_FIRMEZA: {
                'binary_option_pass': 'Se mantiene firme en su posición extendida.',
                'binary_option_fail': 'No se mantiene firme (presenta juego o inestabilidad).',
                'acceptance_criteria': 'Se mantiene firme en su posición extendida.',
            },
            ID_PRESION: {
                'binary_option_pass': 'No colapsa bajo presión simulada.',
                'binary_option_fail': 'Colapsa bajo presión simulada.',
                'acceptance_criteria': 'No colapsa bajo presión simulada.',
            },
        },
        'specs_desactivar': {ID_ABSORCION, ID_EXPULSION},
    },
    {
        'codigo': 'STHIS06', 'rel_vama': 1355,
        'specs_activas': {
            ID_ABSORCION: {'min_value': 140.0, 'max_value': 170.0, 'acceptance_criteria': '140-170 µL'},
        },
        'specs_desactivar': {ID_EXPULSION, ID_EXTENSION, ID_FIRMEZA, ID_PRESION},
    },
]

# ─────────────────────────────────────────────────────────────────
# 4. Ejecutar
# ─────────────────────────────────────────────────────────────────
print("\n── 2. Migrando VAMAs → MAVI-23 ──")
for h in HISOPOS:
    codigo = h['codigo']
    tmpl = Prod.search([('default_code', '=', codigo)], limit=1)
    if not tmpl:
        print(f"  [{codigo}] ADVERTENCIA: producto no encontrado")
        continue

    # Desactivar VAMA
    rel_vama = Rel.browse(h['rel_vama'])
    cfgs_vama = Cfg.search([('product_parameter_rel_id', '=', rel_vama.id)])
    cfgs_vama.write({'active': False})
    rel_vama.write({'active': False})
    print(f"\n  [{codigo}] VAMA desactivado (rel {rel_vama.id})")

    # Crear rel MAVI-23 — _generate_specification_configs crea las 5 configs automáticamente
    rel_mavi23 = Rel.create({
        'product_tmpl_id': tmpl.id,
        'parameter_id': param_mavi23.id,
        'active': True,
    })
    print(f"  [{codigo}] Rel MAVI-23 creada: id {rel_mavi23.id}")

    # Ajustar configs generadas
    cfgs_generadas = Cfg.search([('product_parameter_rel_id', '=', rel_mavi23.id)])
    for cfg in cfgs_generadas:
        spec_id = cfg.specification_id.id if cfg.specification_id else None

        # Desactivar specs que no aplican a este hisopo
        if spec_id in h['specs_desactivar']:
            cfg.write({'active': False})
            continue

        # Aplicar overrides para las specs activas
        overrides = h['specs_activas'].get(spec_id, {})
        if overrides:
            cfg.write(overrides)
            print(f"  [{codigo}]   spec '{cfg.specification_name}' → {overrides}")

env.cr.commit()

# ─────────────────────────────────────────────────────────────────
# 5. Verificación final
# ─────────────────────────────────────────────────────────────────
print("\n── Verificación final ──")
for codigo in ['STHIS01','STHIS02','STHIS03','STHIS04','STHIS05','STHIS06']:
    tmpl = Prod.search([('default_code', '=', codigo)], limit=1)
    if not tmpl:
        continue
    rels = Rel.search([('product_tmpl_id', '=', tmpl.id), ('active', '=', True)])
    print(f"\n  {codigo}:")
    for rel in rels:
        cfgs = Cfg.search([('product_parameter_rel_id', '=', rel.id), ('active', '=', True)])
        for c in cfgs:
            rango = f"{c.min_value}-{c.max_value}" if c.evaluation_type == 'numeric_range' else ''
            binario = f"  pass='{c.binary_option_pass}'" if c.binary_option_pass else ''
            print(f"    {rel.parameter_code}: {c.specification_name} {rango}{binario}")

print("\n✓ Migración completada.")
