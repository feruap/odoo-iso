"""
Corrección MAVI-04: agregar 'Letra adecuada' a los 6 cartuchos especiales que
quedaron fuera del script 20260827_calidad_mavi04_letra_adecuada_cartuchos.py.
Cartuchos: MPCAR26, MPCAR36, MPCAR77, MPCAR78, MPCAR79, MPCAC11.

Nota: MPCAR26, MPCAR36 y MPCAC11 tienen 2 rels de MAVI-04; solo se toca
la rel activa (la que tiene >1 spec activa).
Confirmado por Diana Flores, 2026-08-27.

Idempotente — seguro de correr más de una vez.
Correr UNA VEZ después del deploy a producción.
"""

CARTUCHOS_ESPECIALES = ('MPCAR26', 'MPCAR36', 'MPCAR77', 'MPCAR78', 'MPCAR79', 'MPCAC11')

for code in CARTUCHOS_ESPECIALES:
    # Insertar solo en el rel que ya tiene specs activas (el correcto)
    env.cr.execute("""
        INSERT INTO amunet_quality_parameter_specification_config
          (product_parameter_rel_id, specification_id, specification_name,
           evaluation_type, acceptance_criteria,
           binary_option_pass, binary_option_fail,
           sequence, active, create_uid, write_uid, create_date, write_date)
        SELECT r.id, 702, 'Letra adecuada', 'binary_selection',
          'Información fácil de entender, letra con tono uniforme y definida.',
          'Letra Adecuada', 'Letra No Adecuada',
          10, true, 2, 2, NOW(), NOW()
        FROM amunet_quality_parameter_product_rel r
        JOIN product_template pt ON r.product_tmpl_id = pt.id
        WHERE pt.default_code = %s
          AND r.parameter_code = 'MAVI-04'
          AND (
            SELECT COUNT(*) FROM amunet_quality_parameter_specification_config sc_count
            WHERE sc_count.product_parameter_rel_id = r.id AND sc_count.active = true
          ) > 1
          AND NOT EXISTS (
            SELECT 1 FROM amunet_quality_parameter_specification_config sc2
            WHERE sc2.product_parameter_rel_id = r.id
              AND sc2.specification_name ILIKE '%%letra%%'
              AND sc2.active = true
          )
    """, [code])
    n = env.cr.rowcount
    print(f"{code}: {'Letra adecuada insertada' if n > 0 else 'ya existía (sin cambios)'}")

print("\n✓ Script completado.")
