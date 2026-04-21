"""
create_product_hoja_maestra_antidoping_sangre.py

Crea "Hoja Maestra Antidoping Sangre 2 Parámetros" (SPHMC75)
copiando todos los atributos e imagen del producto base con default_code='SPHMC53'.

Idempotente:
  - Si ya existe con SPHMC75 e imagen → no hace nada.
  - Si ya existe con SPHMC75 pero sin imagen → copia imagen del origen.
  - Si existe con código incorrecto SPHMC53 y nombre correcto → corrige código e imagen.
  - Si no existe → lo crea desde cero.

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

SOURCE_CODE = 'SPHMC53'
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

now = datetime.now(timezone.utc)

def get_source_tmpl_id():
    cur.execute("""
        SELECT pt.id FROM product_template pt
        JOIN product_product pp ON pp.product_tmpl_id = pt.id
        WHERE pp.default_code = %s
        LIMIT 1
    """, (SOURCE_CODE,))
    row = cur.fetchone()
    return row['id'] if row else None

def has_image_attachment(tmpl_id_val):
    cur.execute("""
        SELECT 1 FROM ir_attachment
        WHERE res_model = 'product.template'
          AND res_field = 'image_1920'
          AND res_id = %s
        LIMIT 1
    """, (tmpl_id_val,))
    return cur.fetchone() is not None

def copy_image_attachment(src_tmpl_id_val, dst_tmpl_id_val):
    """Copy image_1920 from ir_attachment of src to dst. Returns True if copied."""
    cur.execute("""
        SELECT name, datas, store_fname, mimetype, file_size
        FROM ir_attachment
        WHERE res_model = 'product.template'
          AND res_field = 'image_1920'
          AND res_id = %s
        ORDER BY id DESC LIMIT 1
    """, (src_tmpl_id_val,))
    src_att = cur.fetchone()
    if not src_att:
        return False
    cur.execute("""
        INSERT INTO ir_attachment
          (name, datas, store_fname, res_model, res_field, res_id,
           type, mimetype, file_size, create_uid, write_uid, create_date, write_date)
        VALUES (%s, %s, %s, 'product.template', 'image_1920', %s,
                'binary', %s, %s, 1, 1, %s, %s)
    """, (
        src_att['name'],
        src_att['datas'],
        src_att['store_fname'],
        dst_tmpl_id_val,
        src_att.get('mimetype', 'image/png'),
        src_att['file_size'],
        now,
        now,
    ))
    return True

def tmpl_has_default_code_col():
    cur.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'product_template'
          AND column_name = 'default_code'
    """)
    return cur.fetchone() is not None

# ── Case 1: correct code SPHMC75 already exists ──────────────────────────────
cur.execute("""
    SELECT pt.id
    FROM product_template pt
    JOIN product_product pp ON pp.product_tmpl_id = pt.id
    WHERE pp.default_code = %s
    LIMIT 1
""", (NEW_CODE,))
row_ok = cur.fetchone()
if row_ok:
    if has_image_attachment(row_ok['id']):
        print(f"[{db}] {NEW_CODE!r} already exists with image — nothing to do.")
        conn.close()
        sys.exit(0)
    src_tmpl_id_for_img = get_source_tmpl_id()
    if src_tmpl_id_for_img and copy_image_attachment(src_tmpl_id_for_img, row_ok['id']):
        conn.commit()
        print(f"[{db}] Updated missing image on {NEW_CODE!r} product (tmpl_id={row_ok['id']}).")
    else:
        print(f"[{db}] {NEW_CODE!r} exists but source has no image — nothing to do.")
    conn.close()
    sys.exit(0)

# ── Case 2: exists with wrong code SPHMC53 + correct name → fix it ───────────
cur.execute("""
    SELECT pt.id, pp.id AS pp_id
    FROM product_template pt
    JOIN product_product pp ON pp.product_tmpl_id = pt.id
    WHERE pp.default_code = %s
      AND pt.name::text ILIKE %s
    LIMIT 1
""", (SOURCE_CODE, f'%{NEW_NAME}%'))
row_bad = cur.fetchone()
if row_bad:
    print(f"[{db}] Found product '{NEW_NAME}' with wrong code {SOURCE_CODE!r} — fixing to {NEW_CODE!r}...")
    cur.execute(
        "UPDATE product_product SET default_code = %s, write_date = %s WHERE id = %s",
        (NEW_CODE, now, row_bad['pp_id']),
    )
    if tmpl_has_default_code_col():
        cur.execute(
            "UPDATE product_template SET default_code = %s, write_date = %s WHERE id = %s",
            (NEW_CODE, now, row_bad['id']),
        )
    if not has_image_attachment(row_bad['id']):
        src_tmpl_id_for_img = get_source_tmpl_id()
        if src_tmpl_id_for_img and copy_image_attachment(src_tmpl_id_for_img, row_bad['id']):
            print(f"[{db}] Also copied missing image from {SOURCE_CODE!r}.")
    conn.commit()
    print(f"[{db}] Fixed: default_code corrected to {NEW_CODE!r} (tmpl_id={row_bad['id']}).")
    conn.close()
    sys.exit(0)

# ── Case 3: product does not exist → create from scratch ─────────────────────
cur.execute("""
    SELECT pt.id FROM product_template pt
    JOIN product_product pp ON pp.product_tmpl_id = pt.id
    WHERE pp.default_code = %s
    LIMIT 1
""", (SOURCE_CODE,))
row = cur.fetchone()
if not row:
    print(f"[{db}] ERROR: Source product not found: default_code={SOURCE_CODE!r}")
    conn.close()
    sys.exit(1)
src_tmpl_id = row['id']
print(f"[{db}] Source product_template.id = {src_tmpl_id} (default_code={SOURCE_CODE})")

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

# default_code excluded here; set explicitly after insert to avoid copying SOURCE_CODE
SKIP_TMPL = {
    'id', 'create_date', 'write_date', 'create_uid', 'write_uid',
    'message_main_attachment_id', 'sequence', 'default_code',
    'website_slug', 'is_published', 'website_published',
    'image_1920',  # stored in ir_attachment in Odoo 17+, not as a column
}

new_tmpl = {}
for col in tmpl_cols:
    if col in SKIP_TMPL or col not in src_tmpl:
        continue
    val = src_tmpl[col]
    if col == 'name':
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

# Set default_code on template if it has a stored column
if 'default_code' in tmpl_cols:
    cur.execute(
        "UPDATE product_template SET default_code = %s WHERE id = %s",
        (NEW_CODE, new_tmpl_id),
    )

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

new_pp = {k: v for k, v in new_pp.items() if k in pp_cols}

cols_p = list(new_pp.keys())
cur.execute(
    f"INSERT INTO product_product ({', '.join(cols_p)}) "
    f"VALUES ({', '.join(f'%({c})s' for c in cols_p)}) RETURNING id",
    new_pp,
)
new_pp_id = cur.fetchone()['id']
print(f"[{db}] Created product_product.id = {new_pp_id}")

# ── Copy image via ir_attachment ──────────────────────────────────────────────
if copy_image_attachment(src_tmpl_id, new_tmpl_id):
    print(f"[{db}] Copied image from {SOURCE_CODE!r} to {NEW_CODE!r} via ir_attachment.")
else:
    print(f"[{db}] No image found for {SOURCE_CODE!r} in ir_attachment — continuing without image.")

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
