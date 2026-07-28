"""
Limpia los spec_configs duplicados de STBAC01 y deja solo los 7 correctos
según el documento ST-010 (CERST-010 / RAST-010).

Resultado final por parámetro:
  MGA 0981  — Variación de volumen      → numeric_range, ≥ 2.5 mL
  MAVI-13   — Partículas en solución    → binary_selection, Sin partículas suspendidas
  MGA 0701  — pH de solución            → numeric_range, 6.9–7.9 (7.4 ± 0.5)
  MAVI-09   — Tiempo de liberación      → numeric_range, 1–30 seg
  MAVI-09   — Tiempo de migración       → numeric_range, 30–180 seg
  MAVI-07   — Muestra negativa          → vama_multi_check, #5 y/o #1-4 (PRB-01)
  MAVI-07   — Muestra positiva          → vama_multi_check, #1-4 y/o #5 (PRB-01)

Idempotente: seguro de correr en cualquier estado de la base de datos.
Correr UNA VEZ después del deploy a producción.
"""
env = env  # noqa: F821 — Odoo shell

Product  = env['product.product']
ParamRel = env['amunet.quality.parameter.product.rel']
SpecCfg  = env['amunet.quality.parameter.specification.config']

product = Product.search([('default_code', '=', 'STBAC01'), ('active', '=', True)], limit=1)
if not product:
    print("ERROR: producto STBAC01 no encontrado")
    raise SystemExit(1)

rels = ParamRel.search([('product_tmpl_id', '=', product.product_tmpl_id.id)])
print(f"STBAC01: {len(rels)} parámetros")

# Specs deseadas por código de parámetro
spec_map = {
    'MGA 0981': [('Variación de volumen',   'numeric_range',    2.5,  999999, '≥ 2.5 mL')],
    'MAVI-13':  [('Partículas en solución', 'binary_selection', 0,    0,      'Sin partículas suspendidas')],
    'MGA 0701': [('pH de solución',         'numeric_range',    6.9,  7.9,    '7.4 ± 0.5')],
    'MAVI-09':  [
        ('Tiempo de liberación', 'numeric_range', 1,   30,  '1 – 30 segundos'),
        ('Tiempo de migración',  'numeric_range', 30,  180, '30 – 180 segundos'),
    ],
    'MAVI-07':  [
        ('Muestra negativa', 'vama_multi_check', 0, 0, '#5 y/o #1-4 (patrón PRB-01)'),
        ('Muestra positiva', 'vama_multi_check', 0, 0, '#1-4 y/o #5 (patrón PRB-01)'),
    ],
}

for rel in rels:
    code = rel.parameter_id.code
    if code not in spec_map:
        print(f"  AVISO: parámetro {code} no mapeado, se omite")
        continue

    desired = spec_map[code]
    all_specs = SpecCfg.search([('product_parameter_rel_id', '=', rel.id)], order='id asc')
    keep_ids = []

    for i, (name, etype, min_v, max_v, criteria) in enumerate(desired):
        if i < len(all_specs):
            sc = all_specs[i]
            sc.write({
                'specification_name': name,
                'evaluation_type': etype,
                'min_value': min_v,
                'max_value': max_v,
                'acceptance_criteria': criteria,
            })
            keep_ids.append(sc.id)
            print(f"  {code}: actualizado sc {sc.id} → {name}")
        else:
            sc = SpecCfg.create({
                'product_parameter_rel_id': rel.id,
                'specification_id': all_specs[0].specification_id.id if all_specs else False,
                'specification_name': name,
                'evaluation_type': etype,
                'min_value': min_v,
                'max_value': max_v,
                'acceptance_criteria': criteria,
                'sequence': (i + 1) * 10,
            })
            keep_ids.append(sc.id)
            print(f"  {code}: creado sc {sc.id} → {name}")

    # Borrar duplicados via SQL para evitar errores de FK
    to_delete_ids = [s.id for s in all_specs if s.id not in keep_ids]
    if to_delete_ids:
        canonical_id = keep_ids[0]
        # Redirigir test_line_details al canónico antes de borrar
        env.cr.execute(
            "UPDATE amunet_quality_test_line_detail "
            "SET specification_config_id = %s "
            "WHERE specification_config_id = ANY(%s)",
            (canonical_id, to_delete_ids)
        )
        redirected = env.cr.rowcount
        env.cr.execute(
            "DELETE FROM amunet_quality_parameter_specification_config "
            "WHERE id = ANY(%s)",
            (to_delete_ids,)
        )
        deleted = env.cr.rowcount
        print(f"  {code}: {deleted} duplicados eliminados ({redirected} tld redirigidos)")

env.cr.commit()
print("LISTO — STBAC01 specs limpiadas. Quedan exactamente 7 specs correctas.")
