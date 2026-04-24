"""
grant_inventory_perms_veronica.py

Otorga permisos completos de inventario a la usuaria
Veronica Ortiz Moncada (supalmacen@amunet.com.mx).

Grupos asignados (buscados por xml_id en ir_model_data):
  stock.group_stock_manager     -- Inventory Manager / Administrador
  stock.group_stock_user        -- Operations / Operaciones
  stock.group_production_lot    -- Lots & Serial Numbers / Lotes
  stock.group_adv_location      -- Advanced Routes / Rutas avanzadas
  stock.group_tracking_lot      -- (solo si existe en Odoo 19)

Idempotente: ON CONFLICT DO NOTHING en la relacion usuario-grupo.

Uso: python3 grant_inventory_perms_veronica.py DB USER PASSWORD HOST PORT
"""
import sys

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psycopg2-binary', '-q'])
    import psycopg2
    import psycopg2.extras

USER_EMAIL = 'supalmacen@amunet.com.mx'

TARGET_GROUPS = [
    ('stock', 'group_stock_manager'),
    ('stock', 'group_stock_user'),
    ('stock', 'group_production_lot'),
    ('stock', 'group_adv_location'),
    ('stock', 'group_tracking_lot'),
]

db   = sys.argv[1]
user = sys.argv[2]
pwd  = sys.argv[3]
host = sys.argv[4]
port = int(sys.argv[5])

print(f"[{db}] Conectando a {host}:{port} como {user}...")
conn = psycopg2.connect(dbname=db, user=user, password=pwd, host=host, port=port)
conn.autocommit = False
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("SELECT id, name FROM res_users WHERE login = %s LIMIT 1", (USER_EMAIL,))
res_user = cur.fetchone()
if not res_user:
    print(f"[ERROR] Usuario '{USER_EMAIL}' no encontrado en '{db}' -- abortando.")
    conn.close()
    sys.exit(1)

uid = res_user['id']
print(f"[OK]   Usuario encontrado: id={uid} name='{res_user['name']}'")

assigned   = []
already    = []
not_found  = []

for module, xml_name in TARGET_GROUPS:
    cur.execute("""
        SELECT imd.res_id AS gid, rg.name AS gname
        FROM ir_model_data imd
        JOIN res_groups rg ON rg.id = imd.res_id
        WHERE imd.module = %s
          AND imd.name   = %s
          AND imd.model  = 'res.groups'
        LIMIT 1
    """, (module, xml_name))
    row = cur.fetchone()

    if not row:
        print(f"[WARN] Grupo '{module}.{xml_name}' no encontrado en '{db}' -- se omite.")
        not_found.append(f'{module}.{xml_name}')
        continue

    gid   = row['gid']
    gname = row['gname']

    cur.execute("""
        SELECT 1 FROM res_groups_users_rel
        WHERE gid = %s AND uid = %s
    """, (gid, uid))
    exists = cur.fetchone()

    if exists:
        print(f"[SKIP] Ya tiene grupo: '{gname}' (gid={gid})")
        already.append(gname)
    else:
        cur.execute("""
            INSERT INTO res_groups_users_rel (gid, uid)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (gid, uid))
        print(f"[OK]   Grupo asignado: '{gname}' (gid={gid})")
        assigned.append(gname)

conn.commit()
conn.close()

print()
print(f"[RESUMEN -- {db}]")
print(f"  Nuevos asignados : {assigned if assigned else 'ninguno'}")
print(f"  Ya tenia         : {already if already else 'ninguno'}")
print(f"  No encontrados   : {not_found if not_found else 'ninguno'}")
print(f"[LISTO] Permisos de inventario actualizados para '{USER_EMAIL}' en '{db}'.")
