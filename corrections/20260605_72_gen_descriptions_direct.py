"""
Genera descripciones de cartuchos directamente en PostgreSQL via psycopg2.
Sin depender del odoo shell.
"""
import re
import json
import psycopg2
from docx import Document

def count_ventanas(c_str):
    if not c_str or 'sin' in c_str.lower():
        return 1
    c_nums = re.findall(r'(\d+)\s*C', c_str)
    if c_nums:
        return sum(int(n) for n in c_nums)
    return 1 if 'C' in c_str.upper() else 1

def clean(s):
    return s.strip().rstrip(',').rstrip('.').strip() if s else ''

# 1. Leer docx
doc = Document('/tmp/F-CC-007-001_full.docx')
cartucho_data = {}

for tabla_idx in [0, 1]:
    for row in doc.tables[tabla_idx].rows[2:]:
        cells = [c.text.strip().replace('\n', ' ') for c in row.cells]
        if len(cells) < 11: continue
        key = cells[0].strip()
        if not key or key in cartucho_data: continue
        desc    = clean(cells[2])
        muestra = clean(cells[3])
        c_str   = cells[9]
        if desc and muestra:
            cartucho_data[key] = {
                'ventanas': count_ventanas(c_str),
                'desc': desc,
                'muestra': muestra
            }

print(f"Datos del documento: {len(cartucho_data)} cartuchos")

# 2. Conectar a PostgreSQL
conn = psycopg2.connect(
    host='odoo-staging-db', port=5432,
    dbname='Amunet_testing', user='odoo', password='odoo_stg_2024_secure'
)
cur = conn.cursor()

# 3. Obtener cartuchos de Odoo
cur.execute("""
    SELECT pt.id, pt.default_code
    FROM product_template pt
    JOIN product_category pc ON pc.id = pt.categ_id
    WHERE pc.name = 'Cartucho' AND pt.default_code IS NOT NULL
""")
productos = cur.fetchall()
print(f"Productos en Odoo: {len(productos)}")

updated, not_found = [], []
for prod_id, default_code in productos:
    code = (default_code or '').strip().upper()
    data = cartucho_data.get(code)
    if not data:
        not_found.append(code)
        continue
    v = data['ventanas']
    desc = (
        f"Cartucho de {v} ventana{'s' if v != 1 else ''} "
        f"para la prueba rápida de {data['desc']} "
        f"usado en muestras {data['muestra']}"
    )
    nueva_desc = json.dumps({"en_US": f"<p>{desc}</p>"})
    cur.execute(
        "UPDATE product_template SET description = %s WHERE id = %s",
        (nueva_desc, prod_id)
    )
    updated.append(f"  {code:<10} {v}V  {data['desc'][:45]}")

conn.commit()
cur.close()
conn.close()

print(f"\n=== ACTUALIZADOS: {len(updated)} ===")
for l in updated[:10]: print(l)
if len(updated) > 10: print(f"  ...y {len(updated)-10} más")
print(f"\nSin datos en doc: {len(not_found)} | {', '.join(not_found[:5])}")
print("Listo.")
