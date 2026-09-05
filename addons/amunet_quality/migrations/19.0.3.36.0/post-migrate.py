# -*- coding: utf-8 -*-
"""
Corrige columnas de anexo en análisis de buffers de proveedor (STBPR01-03, STREX01)
que fueron creados antes de la configuración estándar de 4 columnas.

Aplica: Partículas suspendidas | Liberación | Migración | Desempeño
a todos los análisis donde solo tenían 'Apariencia' (col2 vacía).
"""

BUFFERS = ('STBPR01', 'STBPR02', 'STBPR03', 'STREX01')


def migrate(cr, version):
    placeholders = ','.join(['%s'] * len(BUFFERS))
    cr.execute(f"""
        UPDATE amunet_quality_check qc
        SET anexo_col1_header = 'Partículas suspendidas',
            anexo_col2_header = 'Liberación',
            anexo_col3_header = 'Migración',
            anexo_col4_header = 'Desempeño',
            write_date        = NOW()
        FROM product_product pp
        WHERE pp.id = qc.product_id
          AND pp.default_code IN ({placeholders})
          AND (qc.anexo_col2_header IS NULL OR qc.anexo_col2_header = '')
    """, BUFFERS)
