"""
fix_db_module_descriptions.py
Detecta y corrige TODOS los modulos instalados cuya description en ir_module_module
genera errores de docutils RST. Sustituye el texto fallido por la primera linea
no vacia del propio texto o por un resumen seguro.

Uso: python3 fix_db_module_descriptions.py DB_NAME DB_USER DB_PASSWORD DB_HOST DB_PORT
"""
import sys
import json
import io

try:
    import psycopg2
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psycopg2-binary', '-q'])
    import psycopg2

try:
    import docutils.core
except ImportError:
    print("docutils not available, skipping RST check")
    sys.exit(0)

db   = sys.argv[1] if len(sys.argv) > 1 else 'amunet_prod'
user = sys.argv[2] if len(sys.argv) > 2 else 'odoo'
pwd  = sys.argv[3] if len(sys.argv) > 3 else 'odoo'
host = sys.argv[4] if len(sys.argv) > 4 else 'db'
port = sys.argv[5] if len(sys.argv) > 5 else '5432'


def has_rst_error(text):
    if not text or not text.strip():
        return False
    errout = io.StringIO()
    docutils.core.publish_string(
        source=text,
        writer_name='pseudoxml',
        settings_overrides={'halt_level': 5, 'report_level': 2, 'warning_stream': errout}
    )
    w = errout.getvalue()
    return 'ERROR' in w or 'Unexpected indentation' in w or 'Block quote' in w


def safe_text(text):
    """Returns the first non-empty line of text as a safe single-line replacement."""
    for line in (text or '').splitlines():
        line = line.strip()
        if line:
            return line
    return 'Modulo de Odoo.'


print(f"Connecting to {db} @ {host}:{port} as {user}")
conn = psycopg2.connect(dbname=db, user=user, password=pwd, host=host, port=port)
cur = conn.cursor()

cur.execute("""
    SELECT id, name, description 
    FROM ir_module_module 
    WHERE state IN ('installed', 'to upgrade', 'to install') 
    AND description IS NOT NULL
""")
rows = cur.fetchall()
print(f"Scanning {len(rows)} installed modules with descriptions...")

fixed = 0
for module_id, module_name, desc_raw in rows:
    if not desc_raw:
        continue

    # Parse JSONB
    if isinstance(desc_raw, str):
        try:
            desc_dict = json.loads(desc_raw)
        except Exception:
            continue
    else:
        desc_dict = desc_raw  # psycopg2 auto-parses JSONB to dict

    if not isinstance(desc_dict, dict):
        continue

    changed = False
    new_dict = {}
    for lang, text in desc_dict.items():
        if text and has_rst_error(text):
            replacement = safe_text(text)
            new_dict[lang] = replacement
            print(f"  [FIX] {module_name} [{lang}]: {len(text.splitlines())} lines → '{replacement[:60]}'")
            changed = True
        else:
            new_dict[lang] = text

    if changed:
        cur.execute(
            "UPDATE ir_module_module SET description = %s WHERE id = %s",
            (json.dumps(new_dict), module_id)
        )
        fixed += 1

conn.commit()
conn.close()
print(f"\nDone. Fixed {fixed} module(s) in '{db}'.")
