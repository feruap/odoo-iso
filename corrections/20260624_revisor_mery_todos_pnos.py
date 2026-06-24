"""
Asigna Mery Analit Olivares Vivar (desarrollo@amunet.com.mx) como revisora
en todos los documentos controlados (amunet.documento).
Aplica en producción tras el deploy si revisor_id está vacío.
"""
import psycopg2

conn = psycopg2.connect(host="localhost", dbname="Amunet", user="odoo", password="odoo_prod_password")
cur = conn.cursor()

cur.execute("SELECT id FROM res_users WHERE login = 'desarrollo@amunet.com.mx'")
row = cur.fetchone()
if not row:
    print("ERROR: usuario desarrollo@amunet.com.mx no encontrado")
    conn.close()
    raise SystemExit(1)

mery_id = row[0]
cur.execute("UPDATE amunet_documento SET revisor_id = %s WHERE revisor_id IS NULL", (mery_id,))
print(f"OK: {cur.rowcount} documentos actualizados con revisor_id={mery_id}")

conn.commit()
conn.close()

# Tecnovigilancia: revisor es Stacy Palma (documentacion@amunet.com.mx)
conn2 = psycopg2.connect(host="localhost", dbname="Amunet", user="odoo", password="odoo_prod_password")
cur2 = conn2.cursor()
cur2.execute("SELECT id FROM res_users WHERE login = 'documentacion@amunet.com.mx'")
stacy_id = cur2.fetchone()[0]
cur2.execute("UPDATE amunet_documento SET revisor_id = %s WHERE area = 'TV'", (stacy_id,))
print(f"OK: {cur2.rowcount} PNOs de TV con revisor_id={stacy_id} (Stacy Palma)")
conn2.commit()
conn2.close()
