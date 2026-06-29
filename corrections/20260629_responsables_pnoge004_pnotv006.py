"""
Correcciones de datos — área Documentación (Stacy Palma, 29-jun-2026).
Ejecutar en producción después del deploy de amunet_documentos.

1. PNOGE-004: responsable vacío en actividades 3-12
2. PNOTV-006: responsable vacío en las 3 actividades
3. PNOAL-009: fechas, versión y sustituye_a (CORRER DESPUÉS DEL DEPLOY,
   el documento no existe en producción hasta ese momento)
"""
import psycopg2

conn = psycopg2.connect(host="localhost", dbname="amunet_prod", user="odoo", password="odoo_prod_password")
cur = conn.cursor()

# PNOGE-004: actividades 3 a 12 sin responsable
cur.execute("SELECT id FROM amunet_documento WHERE codigo = 'PNOGE-004'")
doc = cur.fetchone()
if not doc:
    print("ERROR: PNOGE-004 no encontrado")
else:
    cur.execute("""
        UPDATE amunet_documento_actividad
        SET responsable = '<p>Personal que detecta una Desviación / No Conformidad</p>'
        WHERE documento_id = %s
        AND CAST(actividad AS INTEGER) BETWEEN 3 AND 12
        AND (responsable IS NULL OR responsable = '')
    """, (doc[0],))
    print(f"PNOGE-004: {cur.rowcount} actividades actualizadas")

# PNOTV-006: las 3 actividades sin responsable
cur.execute("SELECT id FROM amunet_documento WHERE codigo = 'PNOTV-006'")
doc = cur.fetchone()
if not doc:
    print("ERROR: PNOTV-006 no encontrado")
else:
    cur.execute("""
        UPDATE amunet_documento_actividad
        SET responsable = '<p>Dirección General de Fábrica</p>'
        WHERE documento_id = %s
        AND (responsable IS NULL OR responsable = '')
    """, (doc[0],))
    print(f"PNOTV-006: {cur.rowcount} actividades actualizadas")

# PNOAL-009: fechas, versión y sustituye_a
# (ejecutar DESPUÉS del deploy — el documento llega a producción con el deploy)
cur.execute("SELECT id FROM amunet_documento WHERE codigo = 'PNOAL-009'")
doc = cur.fetchone()
if not doc:
    print("AVISO: PNOAL-009 aún no existe en producción — corre este script después del deploy")
else:
    cur.execute("""
        UPDATE amunet_documento SET
            fecha_emision    = '2023-01-01',
            fecha_vigencia   = '2026-07-01',
            version_actual   = '02',
            sustituye_version = 'PNOAL-009 versión 01'
        WHERE id = %s
    """, (doc[0],))
    print(f"PNOAL-009: fechas, versión y sustituye_a actualizados")

conn.commit()
conn.close()
print("OK: corrección aplicada.")
