"""
create_product_hoja_maestra_antidoping_sangre.py

Crea "Hoja Maestra Antidoping Sangre 2 Parámetros" (SPHMC75)
copiando todos los atributos de "Hoja maestra Antidoping 2 Parámetros".
Idempotente: no hace nada si el producto ya existe.

Uso: python3 create_product_hoja_maestra_antidoping_sangre.py DB USER PASSWORD HOST PORT
"""
import sys
import json
from datetime import datetime, timezone

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psycopg2-binary', '-q'])
    import psycopg2
    import psycopg2.extras

SOURCE_NAME = 'Hoja maestra Antidoping 2 Parámetros'
NEW_NAME    = 'Hoja Maestra Antidoping Sangre 2 Parámetros'
NEW_CODE    = 'SPHMC75'

db   = sys.argv[1] if len(sys.argv) > 1 else 'amunet_prod'
user = sys.argv[2] if len(sys.argv) > 2 else 'odoo'
pwd  = sys.argv[3] if len(sys.argv) > 3 else 'odoo'
host = sys.argv[4] if len(sys.argv) > 4 else 'db'
port = int(sys.argv[5]) if len(sys.argv) > 5 else 5432

print(f"[{db}] Connecting to {host}:{port}")
conn = psycopg2.connect(dbname=db, user=user, password=pwd, host=host, port=port)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# ── Idempotency ──────────────────────────────────────────────────────────────
cur.execute("""
    SELECT pt.id FROM product_template pt
    JOIN product_product pp ON pp.product_tmpl_id = pt.id
    WHERE pp.default_code = %s
    LIMIT 1
""", (NEW_CODE,))
if cur.fetchone():
    print(f"[{db}] {NEW_CODE!r} already exists — nothing to do.")
    conn.close()
    sys.exit(0)

cur.execute("""
    SELECT id FROM product_template
    WHERE name::text ILIKE %s
    LIMIT 1
""", (f'%{NEW_NAME}%',))
if cur.fetchone():
    print(f"[{db}] Product {NEW_NAME!r} already exists — nothing to do.")
    conn.close()
    sys.exit(0)

# ── Find source product ──────────────────────────────────────────────────────
cur.execute("""
    SELECT id FROM product_template
    WHERE name::text ILIKE %s
    LIMIT 1
""", (f'%{SOURCE_NAME}%',))
row = cur.fetchone()
if not row:
    print(f"[{db}] ERROR: Source product not found: {SOURCE_NAME!r}")
    conn.close()
    sys.exit(1)
src_tmpl_id = row['id']
print(f"[{db}] Source product_template.id = {src_tmpl_id}")

# ── Load source rows ─────────────────────────────────────────────────────────
cur.execute("SELECT * FROM product_template WHERE id = %s", (src_tmpl_id,))
src_tmpl = dict(cur.fetchone())

cur.execute("""
    SELECT * FROM product_product
    WHERE product_tmpl_id = %s
    ORDER BY active DESC
    LIMIT 1
""", (src_tmpl_id,))
src_pp_row = cur.fetchone()
src_pp = dict(src_pp_row) if src_pp_row else {}

# ── Get actual column names from information_schema ──────────────────────────
cur.execute("""
    SELECT column_name FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'product_template'
    ORDER BY ordinal_position
""")
tmpl_cols = {r['column_name'] for r in cur.fetchall()}

cur.execute("""
    SELECT column_name FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'product_product'
    ORDER BY ordinal_position
""")
pp_cols = {r['column_name'] for r in cur.fetchall()}

# ── Build new product_template ────────────────────────────────────────────────
SKIP_TMPL = {
    'id', 'create_date', 'write_date', 'create_uid', 'write_uid',
    'message_main_attachment_id', 'sequence',
    'website_slug', 'is_published', 'website_published',
}

now = datetime.now(timezone.utc)

new_tmpl = {}
for col in tmpl_cols:
    if col in SKIP_TMPL or col not in src_tmpl:
        continue
    val = src_tmpl[col]
    if col == 'name':
        # Replace name in every stored language
        if isinstance(val, dict):
            val = {lang: NEW_NAME for lang in val}
        elif isinstance(val, str):
            try:
                parsed = json.loads(val)
                val = {lang: NEW_NAME for lang in parsed} if isinstance(parsed, dict) else NEW_NAME
            except (json.JSONDecodeError, TypeError):
                val = NEW_NAME
        else:
            val = NEW_NAME
    if isinstance(val, (dict, list)):
        val = psycopg2.extras.Json(val)
    new_tmpl[col] = val

new_tmpl.update({
    'create_uid': 1,
    'write_uid': 1,
    'create_date': now,
    'write_date': now,
})

cols_t = list(new_tmpl.keys())
cur.execute(
    f"INSERT INTO product_template ({', '.join(cols_t)}) "
    f"VALUES ({', '.join(f'%({c})s' for c in cols_t)}) RETURNING id",
    new_tmpl,
)
new_tmpl_id = cur.fetchone()['id']
print(f"[{db}] Created product_template.id = {new_tmpl_id}")

# ── Build new product_product ─────────────────────────────────────────────────
SKIP_PP = {
    'id', 'create_date', 'write_date', 'create_uid', 'write_uid',
    'message_main_attachment_id', 'product_tmpl_id', 'default_code',
    'barcode', 'combination_indices',
}

new_pp = {}
for col in pp_cols:
    if col in SKIP_PP or col not in src_pp:
        continue
    val = src_pp[col]
    if isinstance(val, (dict, list)):
        val = psycopg2.extras.Json(val)
    new_pp[col] = val

new_pp.update({
    'product_tmpl_id': new_tmpl_id,
    'default_code': NEW_CODE,
    'active': True,
    'create_uid': 1,
    'write_uid': 1,
    'create_date': now,
    'write_date': now,
})
if 'combination_indices' in pp_cols:
    new_pp['combination_indices'] = ''

# Only include columns that exist in the table
new_pp = {k: v for k, v in new_pp.items() if k in pp_cols}

cols_p = list(new_pp.keys())
cur.execute(
    f"INSERT INTO product_product ({', '.join(cols_p)}) "
    f"VALUES ({', '.join(f'%({c})s' for c in cols_p)}) RETURNING id",
    new_pp,
)
new_pp_id = cur.fetchone()['id']
print(f"[{db}] Created product_product.id = {new_pp_id}")

# ── Copy Many2Many: customer taxes ────────────────────────────────────────────
cur.execute("SELECT tax_id FROM product_taxes_rel WHERE prod_id = %s", (src_tmpl_id,))
taxes = [r['tax_id'] for r in cur.fetchall()]
for tid in taxes:
    cur.execute(
        "INSERT INTO product_taxes_rel (prod_id, tax_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
        (new_tmpl_id, tid),
    )
print(f"[{db}] Copied {len(taxes)} customer tax(es)")

# ── Copy Many2Many: supplier taxes ───────────────────────────────────────────
cur.execute("SELECT tax_id FROM product_supplier_taxes_rel WHERE prod_id = %s", (src_tmpl_id,))
staxes = [r['tax_id'] for r in cur.fetchall()]
for tid in staxes:
    cur.execute(
        "INSERT INTO product_supplier_taxes_rel (prod_id, tax_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
        (new_tmpl_id, tid),
    )
print(f"[{db}] Copied {len(staxes)} supplier tax(es)")

# ── Copy Many2Many: product tags (if table exists) ────────────────────────────
cur.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'product_tag_product_template_rel'
""")
if cur.fetchone():
    cur.execute(
        "SELECT product_tag_id FROM product_tag_product_template_rel WHERE product_template_id = %s",
        (src_tmpl_id,),
    )
    tags = [r['product_tag_id'] for r in cur.fetchall()]
    for tid in tags:
        cur.execute(
            "INSERT INTO product_tag_product_template_rel (product_template_id, product_tag_id) "
            "VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (new_tmpl_id, tid),
        )
    print(f"[{db}] Copied {len(tags)} tag(s)")

conn.commit()
conn.close()
print(f"[{db}] Done: {NEW_NAME!r} [{NEW_CODE}] tmpl_id={new_tmpl_id} pp_id={new_pp_id}")
