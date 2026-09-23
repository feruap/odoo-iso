"""
CORRECCIÓN: etiquetas Ancho/Largo invertidas en MICAJ01-07, MICAJ10-14 (producción)
====================================================================================
En 12 productos de caja, el spec "Ancho" muestra el rango de Largo y viceversa.
El rango numérico está bien; solo se intercambian specification_id y specification_name.

Usa SQL directo (bypass ORM) porque la validación de unicidad bloquea el swap por ORM.
El CASE UPDATE en PostgreSQL es atómico y no dispara la constraint ORM.

Pares (cfg_id_ancho ↔ cfg_id_largo):
  MICAJ01: 70938 ↔ 70939 | MICAJ02: 70949 ↔ 70950 | MICAJ03: 70960 ↔ 70961
  MICAJ04: 70971 ↔ 70972 | MICAJ05: 70982 ↔ 70983 | MICAJ06: 70993 ↔ 70994
  MICAJ07: 71004 ↔ 71005 | MICAJ10: 71037 ↔ 71038 | MICAJ11: 71048 ↔ 71049
  MICAJ12: 71059 ↔ 71060 | MICAJ13: 71070 ↔ 71071 | MICAJ14: 71081 ↔ 71082

Solicitado por: Diana Flores — Control de Calidad, 2026-09-23
"""

PARES = [
    (70938, 70939, 'MICAJ01'),
    (70949, 70950, 'MICAJ02'),
    (70960, 70961, 'MICAJ03'),
    (70971, 70972, 'MICAJ04'),
    (70982, 70983, 'MICAJ05'),
    (70993, 70994, 'MICAJ06'),
    (71004, 71005, 'MICAJ07'),
    (71037, 71038, 'MICAJ10'),
    (71048, 71049, 'MICAJ11'),
    (71059, 71060, 'MICAJ12'),
    (71070, 71071, 'MICAJ13'),
    (71081, 71082, 'MICAJ14'),
]

cr = env.cr

for cfg_a, cfg_l, code in PARES:
    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config AS t
        SET specification_id = swap.new_spec_id,
            specification_name = swap.new_spec_name
        FROM (
            SELECT
                a.id,
                b.specification_id AS new_spec_id,
                b.specification_name AS new_spec_name
            FROM amunet_quality_parameter_specification_config a,
                 amunet_quality_parameter_specification_config b
            WHERE (a.id = %(cfg_a)s AND b.id = %(cfg_l)s)
            UNION ALL
            SELECT
                b.id,
                a.specification_id,
                a.specification_name
            FROM amunet_quality_parameter_specification_config a,
                 amunet_quality_parameter_specification_config b
            WHERE (a.id = %(cfg_a)s AND b.id = %(cfg_l)s)
        ) AS swap
        WHERE t.id = swap.id
    """, {'cfg_a': cfg_a, 'cfg_l': cfg_l})
    print(f"  ✓ {code}: cfg {cfg_a} ↔ cfg {cfg_l}")

env.cr.commit()

# Verificar resultado
print("\nVerificación (muestra MICAJ01, MICAJ07, MICAJ14):")
cr.execute("""
    SELECT pt.default_code, cfg.specification_name, cfg.min_value, cfg.max_value
    FROM amunet_quality_parameter_specification_config cfg
    JOIN amunet_quality_parameter_product_rel rel ON cfg.product_parameter_rel_id = rel.id
    JOIN product_template pt ON rel.product_tmpl_id = pt.id
    WHERE cfg.id IN (70938, 70939, 71004, 71005, 71081, 71082)
    ORDER BY pt.default_code, cfg.specification_name
""")
for row in cr.fetchall():
    print(f"  {row[0]}: {row[1]} = {row[2]}-{row[3]} mm")
