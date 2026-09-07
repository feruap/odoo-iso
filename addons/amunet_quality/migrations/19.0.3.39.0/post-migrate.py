# -*- coding: utf-8 -*-
"""
Goteros — VAMA-038 → MAVI-17 en producción.

1. Desactiva VAMA-038 en todos los STGOT.
2. Activa MAVI-17 con los criterios correctos por gotero.
3. Actualiza los detalles de análisis ABIERTOS que aún referencian VAMA-038,
   y activa has_details en sus test-lines MAVI-17.
4. Aplica ANEXO GOTERO a los análisis abiertos de STGOT sin anexo.
"""

# Criterios de conteo de gotas por producto (min, max, criterio)
MAVI17_CRITERIA = {
    'STGOT01': (5,  15, '10 µl ±5 µl'),
    'STGOT02': (5,  10, '5 a 10 µl ±2 µl'),
    'STGOT03': (15, 25, '20 µl ±5 µl'),
    'STGOT04': (20, 30, '25 µl ±5 µl'),
    'STGOT05': (35, 45, '40 µl ±5 µl'),
    'STGOT06': (35, 45, '40 µl ±5 µl'),
    'STGOT07': (15, 25, '20 µl ±5 µl'),
}

GOTEROS = tuple(MAVI17_CRITERIA.keys())


def migrate(cr, version):
    placeholders = ','.join(['%s'] * len(GOTEROS))

    # 1. Desactivar VAMA-038 en todos los goteros
    cr.execute(f"""
        UPDATE amunet_quality_parameter_specification_config sc
        SET active = false, write_date = NOW()
        FROM amunet_quality_parameter_product_rel r
        JOIN amunet_quality_check_parameter p ON p.id = r.parameter_id
        JOIN product_template pt ON pt.id = r.product_tmpl_id
        WHERE sc.product_parameter_rel_id = r.id
          AND p.code = 'VAMA-038'
          AND pt.default_code IN ({placeholders})
          AND sc.active = true
    """, GOTEROS)

    # 2. Activar MAVI-17 y fijar criterios por gotero
    for code, (mn, mx, crit) in MAVI17_CRITERIA.items():
        cr.execute("""
            UPDATE amunet_quality_parameter_specification_config sc
            SET active              = true,
                specification_name  = 'Conteo de gotas',
                min_value           = %s,
                max_value           = %s,
                acceptance_criteria = %s,
                write_date          = NOW()
            FROM amunet_quality_parameter_product_rel r
            JOIN amunet_quality_check_parameter p ON p.id = r.parameter_id
            JOIN product_template pt ON pt.id = r.product_tmpl_id
            WHERE sc.product_parameter_rel_id = r.id
              AND p.code = 'MAVI-17'
              AND pt.default_code = %s
        """, (mn, mx, crit, code))

    # 3a. Corregir detalles VAMA-038 en análisis ABIERTOS → renombrar a MAVI-17
    cr.execute(f"""
        UPDATE amunet_quality_test_line_detail td
        SET name               = 'Conteo de gotas',
            acceptance_criteria = sc_new.acceptance_criteria,
            min_value           = sc_new.min_value,
            max_value           = sc_new.max_value,
            write_date          = NOW()
        FROM amunet_quality_test_line tl
        JOIN amunet_quality_check qc ON qc.id = tl.check_id
        JOIN amunet_quality_check_parameter p_old ON p_old.id = tl.parameter_id
          AND p_old.code = 'VAMA-038'
        JOIN product_product pp ON pp.id = qc.product_id
        JOIN product_template pt ON pt.id = pp.product_tmpl_id
          AND pt.default_code IN ({placeholders})
        -- Obtener criterios MAVI-17 del mismo producto
        JOIN amunet_quality_parameter_product_rel r_new ON r_new.product_tmpl_id = pt.id
        JOIN amunet_quality_check_parameter p_new ON p_new.id = r_new.parameter_id
          AND p_new.code = 'MAVI-17'
        JOIN amunet_quality_parameter_specification_config sc_new
          ON sc_new.product_parameter_rel_id = r_new.id AND sc_new.active = true
        WHERE td.test_line_id = tl.id
          AND qc.state NOT IN ('approved', 'rejected')
    """, GOTEROS)

    # 3b. Activar has_details en test-lines MAVI-17 de análisis abiertos
    cr.execute(f"""
        UPDATE amunet_quality_test_line tl
        SET has_details = true, write_date = NOW()
        FROM amunet_quality_check qc
        JOIN product_product pp ON pp.id = qc.product_id
        JOIN product_template pt ON pt.id = pp.product_tmpl_id
        JOIN amunet_quality_check_parameter p ON p.id = tl.parameter_id
          AND p.code = 'MAVI-17'
        WHERE tl.check_id = qc.id
          AND pt.default_code IN ({placeholders})
          AND qc.state NOT IN ('approved', 'rejected')
          AND (tl.has_details IS NULL OR tl.has_details = false)
    """, GOTEROS)

    # 4. Aplicar ANEXO GOTERO a análisis abiertos sin anexo configurado
    cr.execute(f"""
        UPDATE amunet_quality_check qc
        SET is_material_con_anexo = true,
            anexo_titulo          = 'ANEXO GOTERO',
            anexo_col1_header     = 'Determinación de aspectos',
            anexo_col2_header     = 'Punta del gotero (mm)',
            anexo_col3_header     = 'Largo del gotero (mm)',
            anexo_col4_header     = 'Volumen (µL)',
            write_date            = NOW()
        FROM product_product pp
        JOIN product_template pt ON pt.id = pp.product_tmpl_id
        WHERE pp.id = qc.product_id
          AND pt.default_code IN ({placeholders})
          AND qc.state NOT IN ('approved', 'rejected')
          AND (qc.anexo_col1_header IS NULL OR qc.anexo_col1_header = ''
               OR qc.anexo_col1_header = 'Apariencia')
    """, GOTEROS)
