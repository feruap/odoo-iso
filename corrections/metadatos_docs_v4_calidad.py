# Metadatos de documentos del SGC: sube reportes y certificados a VERSION 4,
# vigencia 2026-07-01 a 2029-07-01 (reemplaza v3), para todos los productos
# que tienen analisis de calidad. Solicitado por Agente Calidad (Diana Flores).
# Autorizado por Fernando 2026-07-21. NO toca precios.
env.cr.execute("""
    SELECT count(DISTINCT pp.product_tmpl_id)
    FROM amunet_quality_check qc
    JOIN product_product pp ON pp.id = qc.product_id
""")
n = env.cr.fetchone()[0]
print('Productos con analisis a actualizar:', n)

print('ANTES (report_version, cert_version -> count):')
env.cr.execute("""
    SELECT report_version, certificate_version, count(*)
    FROM product_template pt
    WHERE pt.id IN (SELECT DISTINCT pp.product_tmpl_id
                    FROM amunet_quality_check qc
                    JOIN product_product pp ON pp.id = qc.product_id)
    GROUP BY 1,2 ORDER BY 3 DESC
""")
for row in env.cr.fetchall():
    print('  ', row)

env.cr.execute("""
    UPDATE product_template pt
    SET report_effective_date='2026-07-01', report_expiry_date='2029-07-01',
        report_version=4, report_replaces_version=3,
        certificate_effective_date='2026-07-01', certificate_expiry_date='2029-07-01',
        certificate_version=4, certificate_replaces_version=3
    WHERE pt.id IN (SELECT DISTINCT pp.product_tmpl_id
                    FROM amunet_quality_check qc
                    JOIN product_product pp ON pp.id = qc.product_id)
""")
print('Filas actualizadas:', env.cr.rowcount)
env.cr.commit()
env.invalidate_all()

print('DESPUES (report_version, cert_version -> count):')
env.cr.execute("""
    SELECT report_version, certificate_version, count(*)
    FROM product_template pt
    WHERE pt.id IN (SELECT DISTINCT pp.product_tmpl_id
                    FROM amunet_quality_check qc
                    JOIN product_product pp ON pp.id = qc.product_id)
    GROUP BY 1,2 ORDER BY 3 DESC
""")
for row in env.cr.fetchall():
    print('  ', row)
print('LISTO')
