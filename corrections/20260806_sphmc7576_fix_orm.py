"""
Fix para SPHMC75 y SPHMC76: limpia specs duplicadas via ORM para que el
sistema reconozca las specs correctas y no las regenere desde la plantilla.

Rels afectados:
  SPHMC75: MAVI-04=3186, MAVI-09=3189, MAVI-11=3190
  SPHMC76: MAVI-04=3187, MAVI-09=3192, MAVI-11=3193

Confirmado por Diana Flores, 2026-08-06:
  MAVI-09: Liberación 1-30 s / Migración 30-180 s (estándar)
  MAVI-07: Competitiva (2 specs ya correctas — no se tocan)
  MAVI-11: Altura 6 u 8 cm ± 0.5 cm (conditional_numeric_range, spec_id=414)
"""

SpecConfig = env['amunet.quality.parameter.specification.config']
ParamRel   = env['amunet.quality.parameter.product.rel']

RELS = {
    'SPHMC75': {'mavi04': 3186, 'mavi09': 3189, 'mavi11': 3190},
    'SPHMC76': {'mavi04': 3187, 'mavi09': 3192, 'mavi11': 3193},
}

MAVI04_SPECS = [
    {'specification_id': 1,   'specification_name': 'Polvo',                  'evaluation_type': 'binary_selection', 'min_value': 0, 'max_value': 0, 'acceptance_criteria': 'Sin polvo',                  'sequence': 10},
    {'specification_id': 170, 'specification_name': 'Rasgaduras',             'evaluation_type': 'binary_selection', 'min_value': 0, 'max_value': 0, 'acceptance_criteria': 'Sin rasgaduras',             'sequence': 20},
    {'specification_id': 171, 'specification_name': 'Manchas y/o suciedad',   'evaluation_type': 'binary_selection', 'min_value': 0, 'max_value': 0, 'acceptance_criteria': 'Sin manchas y/o suciedad',   'sequence': 30},
    {'specification_id': 175, 'specification_name': 'Deformidad o deterioro', 'evaluation_type': 'binary_selection', 'min_value': 0, 'max_value': 0, 'acceptance_criteria': 'Sin deformidad o deterioro', 'sequence': 40},
    {'specification_id': 190, 'specification_name': 'Sellado',                'evaluation_type': 'binary_selection', 'min_value': 0, 'max_value': 0, 'acceptance_criteria': '',                           'sequence': 50},
]

MAVI09_SPECS = [
    {'specification_id': 146, 'specification_name': 'Liberación de conjugado', 'evaluation_type': 'numeric_range', 'min_value': 1,  'max_value': 30,  'acceptance_criteria': '1 a 30 segundos',   'sequence': 10},
    {'specification_id': 126, 'specification_name': 'Migración de conjugado',  'evaluation_type': 'numeric_range', 'min_value': 30, 'max_value': 180, 'acceptance_criteria': '30 a 180 segundos', 'sequence': 20},
]

MAVI11_SPECS = [
    {'specification_id': 414, 'specification_name': 'Altura 6 u 8 cm (según aplique)', 'evaluation_type': 'conditional_numeric_range', 'min_value': 0, 'max_value': 0, 'acceptance_criteria': '6 u 8 cm ± 0.5 cm', 'sequence': 10},
]

for codigo, rels in RELS.items():
    print(f"\n── {codigo} ───────────────────────────────────")

    for param, rel_id, specs in [
        ('MAVI-04', rels['mavi04'], MAVI04_SPECS),
        ('MAVI-09', rels['mavi09'], MAVI09_SPECS),
        ('MAVI-11', rels['mavi11'], MAVI11_SPECS),
    ]:
        rel = ParamRel.browse(rel_id)
        # Borrar via ORM para que el cache se actualice
        existing = rel.specification_config_ids
        print(f"  {param}: eliminando {len(existing)} specs existentes via ORM")
        existing.unlink()
        env.flush_all()

        # Crear las specs correctas via ORM
        for spec_vals in specs:
            vals = dict(spec_vals)
            vals['product_parameter_rel_id'] = rel_id
            SpecConfig.create(vals)
        env.flush_all()
        print(f"  {param}: {len(specs)} specs correctas creadas via ORM")

        # Verificar
        final_count = len(rel.specification_config_ids)
        print(f"  {param}: verificación → {final_count} specs en rel {rel_id}")

env.cr.commit()
print("\nLISTO — SPHMC75 y SPHMC76 configurados via ORM (cache actualizado).")
