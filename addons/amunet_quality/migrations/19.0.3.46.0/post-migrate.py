# -*- coding: utf-8 -*-
"""
Agrega descripción a STBPR01-04 y STREX01/02 en producto y análisis abiertos.
"""
import json

DESCRIPCIONES = {
    'STBPR01': 'Solución de corrimiento para pruebas con muestras de sangre, suero y plasma',
    'STBPR02': 'Solución de corrimiento para pruebas con muestras nasofaríngeas u orofaríngeas',
    'STBPR03': 'Solución de corrimiento para pruebas con muestras de heces',
    'STBPR04': 'Solución de corrimiento para pruebas con muestras de hisopados vaginales o uretrales',
    'STREX01': 'Reactivo de extracción 1',
    'STREX02': 'Reactivo de extracción 2',
}


def migrate(cr, version):
    import logging
    _logger = logging.getLogger(__name__)

    for code, desc in DESCRIPCIONES.items():
        desc_json = json.dumps({'en_US': f'<p>{desc}</p>', 'es_MX': f'<p>{desc}</p>'})

        # 1. Producto (para futuros análisis)
        cr.execute("""
            UPDATE product_template
            SET description = %s::jsonb, write_date = NOW()
            WHERE default_code = %s
              AND (description IS NULL OR description::text = 'null')
        """, (desc_json, code))
        _logger.info("%s descripción en producto: %d", code, cr.rowcount)

        # 2. Análisis abiertos sin descripción
        cr.execute("""
            UPDATE amunet_quality_check qc
            SET product_description = %s::jsonb, write_date = NOW()
            FROM product_product pp
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE pp.id = qc.product_id
              AND pt.default_code = %s
              AND qc.state NOT IN ('approved', 'rejected', 'done')
              AND (qc.product_description IS NULL
                   OR qc.product_description::text = 'null'
                   OR qc.product_description::text = '{}')
        """, (desc_json, code))
        _logger.info("%s descripción en análisis abiertos: %d", code, cr.rowcount)
