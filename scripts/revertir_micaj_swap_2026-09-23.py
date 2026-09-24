# Revertir el swap Ancho/Largo — el original era correcto según el documento
# Ancho=110mm (105-115), Largo=200mm (195-205)
# El swap anterior lo dejó al revés.

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
            SELECT a.id, b.specification_id AS new_spec_id, b.specification_name AS new_spec_name
            FROM amunet_quality_parameter_specification_config a,
                 amunet_quality_parameter_specification_config b
            WHERE a.id = %(a)s AND b.id = %(b)s
            UNION ALL
            SELECT b.id, a.specification_id, a.specification_name
            FROM amunet_quality_parameter_specification_config a,
                 amunet_quality_parameter_specification_config b
            WHERE a.id = %(a)s AND b.id = %(b)s
        ) AS swap
        WHERE t.id = swap.id
    """, {'a': cfg_a, 'b': cfg_l})
    print(f"  ✓ {code} revertido")

env.cr.commit()

print("\nVerificación (MICAJ01, MICAJ14):")
cr.execute("""
    SELECT pt.default_code, cfg.specification_name, cfg.min_value, cfg.max_value
    FROM amunet_quality_parameter_specification_config cfg
    JOIN amunet_quality_parameter_product_rel rel ON cfg.product_parameter_rel_id = rel.id
    JOIN product_template pt ON rel.product_tmpl_id = pt.id
    WHERE cfg.id IN (70938, 70939, 71081, 71082)
    ORDER BY pt.default_code, cfg.specification_name
""")
for row in cr.fetchall():
    print(f"  {row[0]}: {row[1]} = {row[2]}-{row[3]} mm")
