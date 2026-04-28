"""
create_product_lengueta_len01.py

Crea "Lengüeta" (LEN01)
copiando todos los atributos e imagen del producto base con default_code='DSC01'.

Idempotente:
  - Si ya existe con LEN01 e imagen → no hace nada.
  - Si ya existe con LEN01 pero sin imagen → copia imagen del origen.
  - Si existe con código incorrecto DSC01 y nombre correcto → corrige código e imagen.
  - Si no existe → lo crea desde cero.

Uso: python3 create_product_lengueta_len01.py DB USER PASSWORD HOST PORT
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

SOURCE_CODE = 'DSC01'
NEW_NAME    = 'Lengüeta'
NEW_CODE    = 'LEN01'

db   = sys.argv[1]
user = sys.argv[2]
pwd  = sys.argv[3]
host = sys.argv[4]
port = int(sys.argv[5])

print(f"[{db}] Conectando a {host}:{port} como {user}...")
conn = psycopg2.connect(dbname=db, user=user, password=pwd, host=host, port=port)
conn.autocommit = False
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

now = datetime.now(timezone.utc)

# ── Helpers ────────────────────────────────────────────────────────────────────

def get_ir_attachment_cols():
    """Devuelve el conjunto de columnas que tiene ir_attachment en esta instancia."""
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'ir_attachment'
    """)
    return {r['column_name'] for r in cur.fetchall()}

def fix_codes(tmpl_id, pp_id):
    """Actualiza default_code en product_product y product_template (si aplica)."""
    cur.execute("""
        UPDATE product_product SET default_code = %s
        WHERE id = %s AND (default_code != %s OR default_code IS NULL)
    """, (NEW_CODE, pp_id, NEW_CODE))
    updated = cur.rowcount
    if updated:
        print(f"[OK]   product_product id={pp_id} default_code → '{NEW_CODE}'")
    else:
        print(f"[OK]   product_product id={pp_id} default_code ya es '{NEW_CODE}'")

    cur.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='product_template'
          AND column_name='default_code'
    """)
    if cur.fetchone():
        cur.execute("UPDATE product_template SET default_code = %s WHERE id = %s",
                    (NEW_CODE, tmpl_id))
        print(f"[OK]   product_template id={tmpl_id} default_code → '{NEW_CODE}'")
    else:
        print(f"[INFO] product_template no tiene columna default_code (normal en Odoo 17+)")

def has_image(tmpl_id):
    cur.execute("""
        SELECT id FROM ir_attachment
        WHERE res_model='product.template' AND res_field='image_1920' AND res_id=%s
        LIMIT 1
    """, (tmpl_id,))
    return cur.fetchone() is not None

def copy_image(src_id, dst_id):
    """
    Copia imagen desde template src_id a dst_id via ir_attachment.
    Incluye checksum (SHA1) si la columna existe — obligatorio en Odoo 17+ para servir imágenes.
    """
    existing_cols = get_ir_attachment_cols()

    base_cols = ['id', 'name', 'mimetype', 'store_fname', 'file_size']
    if 'checksum' in existing_cols:
        base_cols.append('checksum')
    sel = ', '.join(base_cols)

    cur.execute(f"""
        SELECT {sel} FROM ir_attachment
        WHERE res_model='product.template' AND res_field='image_1920' AND res_id=%s
        ORDER BY id DESC LIMIT 1
    """, (src_id,))
    att = cur.fetchone()

    if not att:
        cur.execute(f"""
            SELECT {sel} FROM ir_attachment
            WHERE res_model='product.template' AND res_id=%s
              AND mimetype ILIKE 'image/%'
            ORDER BY id DESC LIMIT 1
        """, (src_id,))
        att = cur.fetchone()
        if not att:
            print(f"[WARN] No hay imagen en ir_attachment para src_id={src_id} — se omite")
            return False
        print(f"[INFO] Imagen encontrada via fallback mimetype: id={att['id']}")

    if not att.get('store_fname'):
        print(f"[WARN] Attachment id={att['id']} sin store_fname — no se puede copiar")
        return False

    checksum_val = att.get('checksum') if att.get('checksum') else None
    if not checksum_val and att.get('store_fname') and '/' in att['store_fname']:
        checksum_val = att['store_fname'].split('/')[-1]
        print(f"[INFO] checksum derivado de store_fname: {checksum_val}")
    elif checksum_val:
        print(f"[INFO] checksum copiado del origen: {checksum_val}")

    print(f"[INFO] Imagen origen: id={att['id']}, mimetype={att['mimetype']}, "
          f"store_fname={att['store_fname']}, file_size={att['file_size']}")

    cur.execute("""
        DELETE FROM ir_attachment
        WHERE res_model='product.template' AND res_field='image_1920' AND res_id=%s
    """, (dst_id,))

    data = {
        'name':        att['name'] or 'image',
        'res_model':   'product.template',
        'res_field':   'image_1920',
        'res_id':      dst_id,
        'type':        'binary',
        'mimetype':    att['mimetype'] or 'image/jpeg',
        'store_fname': att['store_fname'],
        'file_size':   att['file_size'] or 0,
        'create_date': now,
        'write_date':  now,
    }

    optional = {
        'res_name':   NEW_NAME,
        'public':     False,
        'create_uid': 1,
        'write_uid':  1,
    }
    for col, val in optional.items():
        if col in existing_cols:
            data[col] = val

    if 'checksum' in existing_cols and checksum_val:
        data['checksum'] = checksum_val

    cols = list(data.keys())
    vals = [data[c] for c in cols]

    cur.execute("SAVEPOINT img_copy")
    try:
        cur.execute(
            f"INSERT INTO ir_attachment ({','.join(cols)}) VALUES ({','.join(['%s']*len(vals))})",
            vals
        )
        cur.execute("RELEASE SAVEPOINT img_copy")
        print(f"[OK]   Imagen copiada a dst_tmpl_id={dst_id} (checksum={'incluido' if checksum_val else 'no disponible'})")
        return True
    except Exception as e:
        cur.execute("ROLLBACK TO SAVEPOINT img_copy")
        print(f"[ERROR] Fallo al insertar imagen: {e}")
        return False


# ── Case 1: LEN01 ya existe con imagen ────────────────────────────────────────
cur.execute("""
    SELECT pt.id, pp.id AS pp_id
    FROM product_template pt
    JOIN product_product pp ON pp.product_tmpl_id = pt.id
    WHERE pp.default_code = %s
    LIMIT 1
""", (NEW_CODE,))
row = cur.fetchone()

if row:
    tmpl_id, pp_id = row['id'], row['pp_id']
    fix_codes(tmpl_id, pp_id)

    if has_image(tmpl_id):
        print(f"[{db}] '{NEW_CODE}' ya existe con imagen — nothing to do.")
        conn.commit(); conn.close(); sys.exit(0)

    print(f"[{db}] '{NEW_CODE}' existe pero sin imagen — copiando...")
    cur.execute("""
        SELECT pt.id FROM product_template pt
        JOIN product_product pp ON pp.product_tmpl_id = pt.id
        WHERE pp.default_code = %s LIMIT 1
    """, (SOURCE_CODE,))
    src_row = cur.fetchone()
    if src_row:
        copy_image(src_row['id'], tmpl_id)
    conn.commit(); conn.close()
    print(f"[LISTO] Imagen actualizada en '{db}'.")
    sys.exit(0)


# ── Case 2: Existe con código incorrecto (DSC01 + nombre correcto) ─────────────
cur.execute("""
    SELECT pt.id, pp.id AS pp_id
    FROM product_template pt
    JOIN product_product pp ON pp.product_tmpl_id = pt.id
    WHERE pp.default_code = %s
      AND (pt.name::text ILIKE %s OR pt.name::text ILIKE %s)
    LIMIT 1
""", (SOURCE_CODE, f'%{NEW_NAME}%', '%Leng%eta%'))
row = cur.fetchone()

if row:
    tmpl_id, pp_id = row['id'], row['pp_id']
    print(f"[{db}] Código incorrecto encontrado (tmpl_id={tmpl_id}) — corrigiendo...")
    fix_codes(tmpl_id, pp_id)

    if not has_image(tmpl_id):
        cur.execute("""
            SELECT pt.id FROM product_template pt
            JOIN product_product pp ON pp.product_tmpl_id = pt.id
            WHERE pp.default_code = %s LIMIT 1
        """, (SOURCE_CODE,))
        src_row = cur.fetchone()
        if src_row:
            copy_image(src_row['id'], tmpl_id)
    else:
        print(f"[OK]   Imagen ya existe — sin cambios")

    conn.commit(); conn.close()
    print(f"[LISTO] Código e imagen corregidos en '{db}'.")
    sys.exit(0)


# ── Case 3: No existe — crear desde cero ──────────────────────────────────────
print(f"[{db}] Producto '{NEW_CODE}' no existe — creando desde cero...")

cur.execute("""
    SELECT pt.id FROM product_template pt
    JOIN product_product pp ON pp.product_tmpl_id = pt.id
    WHERE pp.default_code = %s LIMIT 1
""", (SOURCE_CODE,))
src_row = cur.fetchone()
if not src_row:
    print(f"[ERROR] Producto base '{SOURCE_CODE}' no encontrado en '{db}' — abortando.")
    conn.close(); sys.exit(1)

src_tmpl_id = src_row['id']
print(f"[OK]   Producto base encontrado: tmpl_id={src_tmpl_id}")

SKIP_TMPL = {'id', 'create_date', 'write_date', 'create_uid', 'write_uid',
             'default_code', 'image_1920', 'image_128', 'active'}

cur.execute("""
    SELECT column_name FROM information_schema.columns
    WHERE table_schema='public' AND table_name='product_template'
    ORDER BY ordinal_position
""")
all_tmpl_cols = [r['column_name'] for r in cur.fetchall()]
copy_cols = [c for c in all_tmpl_cols if c not in SKIP_TMPL]

cur.execute(f"SELECT {', '.join(copy_cols)} FROM product_template WHERE id = %s", (src_tmpl_id,))
src_row = cur.fetchone()

cols_str = ', '.join(copy_cols + ['default_code', 'active', 'create_date', 'write_date'])
vals_placeholder = ', '.join(['%s'] * (len(copy_cols) + 4))
values = [src_row[c] for c in copy_cols] + [NEW_CODE, True, now, now]

if 'name' in copy_cols:
    name_idx = copy_cols.index('name')
    try:
        orig_name = src_row['name']
        if isinstance(orig_name, dict):
            new_name_val = {k: NEW_NAME for k in orig_name.keys()}
        elif isinstance(orig_name, str):
            try:
                parsed = json.loads(orig_name)
                new_name_val = {k: NEW_NAME for k in parsed.keys()}
            except Exception:
                new_name_val = NEW_NAME
        else:
            new_name_val = NEW_NAME
        values[name_idx] = json.dumps(new_name_val) if isinstance(new_name_val, dict) else new_name_val
    except Exception as e:
        print(f"[WARN] No se pudo parsear name JSONB: {e} — usando string directo")
        values[name_idx] = NEW_NAME

# Serializar JSONB antes de INSERT (psycopg2 no adapta dict automáticamente)
values = [json.dumps(v) if isinstance(v, dict) else v for v in values]

cur.execute(f"""
    INSERT INTO product_template ({cols_str})
    VALUES ({vals_placeholder})
    RETURNING id
""", values)
new_tmpl_id = cur.fetchone()['id']
print(f"[OK]   product_template creado: id={new_tmpl_id}")

cur.execute("SELECT id FROM product_product WHERE product_tmpl_id = %s LIMIT 1", (src_tmpl_id,))
src_pp = cur.fetchone()

SKIP_PP = {'id', 'create_date', 'write_date', 'create_uid', 'write_uid',
           'product_tmpl_id', 'default_code', 'active'}

cur.execute("""
    SELECT column_name FROM information_schema.columns
    WHERE table_schema='public' AND table_name='product_product'
    ORDER BY ordinal_position
""")
all_pp_cols = [r['column_name'] for r in cur.fetchall()]
copy_pp_cols = [c for c in all_pp_cols if c not in SKIP_PP]

if src_pp:
    cur.execute(f"SELECT {', '.join(copy_pp_cols)} FROM product_product WHERE id = %s", (src_pp['id'],))
    src_pp_row = cur.fetchone()
    pp_cols_str = ', '.join(copy_pp_cols + ['product_tmpl_id', 'default_code', 'active', 'create_date', 'write_date'])
    pp_vals = [src_pp_row[c] for c in copy_pp_cols] + [new_tmpl_id, NEW_CODE, True, now, now]
else:
    pp_cols_str = 'product_tmpl_id, default_code, active, create_date, write_date'
    pp_vals = [new_tmpl_id, NEW_CODE, True, now, now]

# Serializar JSONB antes de INSERT
pp_vals = [json.dumps(v) if isinstance(v, dict) else v for v in pp_vals]

pp_placeholder = ', '.join(['%s'] * len(pp_vals))
cur.execute(f"""
    INSERT INTO product_product ({pp_cols_str})
    VALUES ({pp_placeholder})
    RETURNING id
""", pp_vals)
new_pp_id = cur.fetchone()['id']
print(f"[OK]   product_product creado: id={new_pp_id} default_code='{NEW_CODE}'")

copy_image(src_tmpl_id, new_tmpl_id)

conn.commit(); conn.close()
print(f"[LISTO] Producto '{NEW_CODE}' creado correctamente en '{db}'.")
