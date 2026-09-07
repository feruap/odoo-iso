# -*- coding: utf-8 -*-
"""
Goteros STGOT01-07:
1. Elimina test_lines VAMA-038 en análisis ABIERTOS (no done/approved/rejected)
   — ya fueron reemplazadas por MAVI-17 en la mig 39.0.
2. Pone la descripción del material en análisis abiertos y en el producto
   (goteros STGOT01-07 y buffers STBBM01/STBBM02).
"""
import json

GOTEROS = ('STGOT01', 'STGOT02', 'STGOT03', 'STGOT04', 'STGOT05', 'STGOT06', 'STGOT07')

DESCRIPCIONES = {
    'STGOT01': 'Gotero usado para la transferencia de muestra de 10 µl',
    'STGOT02': 'Gotero usado para la transferencia de muestra de 5 µl',
    'STGOT03': 'Gotero usado para la transferencia de muestra de 20 µl',
    'STGOT04': 'Gotero usado para la transferencia de muestra de 25 µl',
    'STGOT05': 'Gotero usado para la transferencia de muestra de 40 µl',
    'STGOT06': 'Gotero usado para la transferencia de muestra de 40 µl',
    'STGOT07': 'Gotero usado para la transferencia de muestra de 20 µl',
    'STBBM01': 'Vial de Solución de corrimiento usado para pruebas de BIONET MULTI en PCR rápida, con volumen de 90-120 microlitros',
    'STBBM02': 'Vial de Solución de corrimiento usado para pruebas de BIONET MULTI en PCR rápida, con volumen de 250 microlitros',
}

ESTADOS_ABIERTOS = ('approved', 'rejected', 'done')


def migrate(cr, version):
    import logging
    _logger = logging.getLogger(__name__)

    ph = ','.join(['%s'] * len(GOTEROS))

    # 0. CONVERTIR las lineas que la mig 39.0 ya reutilizo, ANTES de borrar.
    #
    # La 39.0 no crea una linea MAVI-17 nueva: reaprovecha la linea VAMA-038 y le
    # cambia el contenido a 'Conteo de gotas' con el rango del gotero. La linea
    # sigue apuntando al parametro viejo, asi que los borrados de 1a/1b se la
    # llevan y el analisis se queda SIN medicion de volumen (verificado sobre
    # clon de produccion: los 4 analisis abiertos perdian la linea completa).
    #
    # Aqui se repunta al parametro correcto y se renombra. Lo que quede con
    # VAMA-038 despues de esto si es residuo real y lo borran 1a/1b.
    cr.execute(f"""
        UPDATE amunet_quality_test_line tl
        SET parameter_id = (SELECT id FROM amunet_quality_check_parameter
                            WHERE code = 'MAVI-17' LIMIT 1),
            name         = 'Determinación de volumen',
            code         = 'MAVI-17',
            write_date   = NOW()
        FROM amunet_quality_check qc
        JOIN product_product pp ON pp.id = qc.product_id
        JOIN product_template pt ON pt.id = pp.product_tmpl_id,
             amunet_quality_check_parameter p
        WHERE tl.check_id = qc.id
          AND p.id = tl.parameter_id
          AND p.code = 'VAMA-038'
          AND pt.default_code IN ({ph})
          AND qc.state NOT IN ('approved', 'rejected', 'done')
          AND EXISTS (SELECT 1 FROM amunet_quality_test_line_detail d
                      WHERE d.test_line_id = tl.id AND d.name = 'Conteo de gotas')
    """, GOTEROS)
    _logger.info("Goteros: lineas VAMA-038 convertidas a MAVI-17: %d", cr.rowcount)

    # 1a. Borrar detalles de VAMA-038 en análisis activos (en_curso, borrador)
    cr.execute(f"""
        DELETE FROM amunet_quality_test_line_detail d
        USING amunet_quality_test_line tl
        JOIN amunet_quality_check qc ON qc.id = tl.check_id
        JOIN product_product pp ON pp.id = qc.product_id
        JOIN product_template pt ON pt.id = pp.product_tmpl_id
        JOIN amunet_quality_check_parameter p ON p.id = tl.parameter_id
        WHERE d.test_line_id = tl.id
          AND p.code = 'VAMA-038'
          AND pt.default_code IN ({ph})
          AND qc.state NOT IN ('approved', 'rejected', 'done')
    """, GOTEROS)
    _logger.info("Goteros VAMA-038 detalles eliminados: %d", cr.rowcount)

    # 1b. Borrar test_lines VAMA-038 en análisis activos
    cr.execute(f"""
        DELETE FROM amunet_quality_test_line tl
        USING amunet_quality_check qc
        JOIN product_product pp ON pp.id = qc.product_id
        JOIN product_template pt ON pt.id = pp.product_tmpl_id,
             amunet_quality_check_parameter p
        WHERE tl.check_id = qc.id
          AND p.id = tl.parameter_id
          AND p.code = 'VAMA-038'
          AND pt.default_code IN ({ph})
          AND qc.state NOT IN ('approved', 'rejected', 'done')
    """, GOTEROS)
    _logger.info("Goteros VAMA-038 test_lines eliminadas: %d", cr.rowcount)

    # 2a. Descripción en análisis activos de cada gotero
    for code, desc in DESCRIPCIONES.items():
        desc_json = json.dumps({'en_US': f'<p>{desc}</p>', 'es_MX': f'<p>{desc}</p>'})
        cr.execute("""
            UPDATE amunet_quality_check qc
            SET product_description = %s::jsonb, write_date = NOW()
            FROM product_product pp
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE pp.id = qc.product_id
              AND pt.default_code = %s
              AND qc.state NOT IN ('approved', 'rejected', 'done')
              AND qc.product_description IS NULL
        """, (desc_json, code))
        _logger.info("STGOT %s descripción en análisis: %d filas", code, cr.rowcount)

    # 2b. Descripción en producto (para análisis futuros)
    for code, desc in DESCRIPCIONES.items():
        desc_json = json.dumps({'en_US': f'<p>{desc}</p>', 'es_MX': f'<p>{desc}</p>'})
        cr.execute("""
            UPDATE product_template
            SET description = %s::jsonb, write_date = NOW()
            WHERE default_code = %s
              AND (description IS NULL OR description::text = 'null')
        """, (desc_json, code))
