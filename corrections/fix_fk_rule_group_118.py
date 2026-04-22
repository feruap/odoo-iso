"""
fix_fk_rule_group_118.py

Elimina la fila huerfana rule_group_rel.group_id = 118 que causa FK violation
en Amunet_testing durante -u all. Idempotente.

Uso: python3 fix_fk_rule_group_118.py DB USER PASSWORD HOST PORT
"""
import sys

try:
    import psycopg2
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psycopg2-binary', '-q'])
    import psycopg2

db   = sys.argv[1] if len(sys.argv) > 1 else 'Amunet_testing'
user = sys.argv[2] if len(sys.argv) > 2 else 'odoo'
pwd  = sys.argv[3] if len(sys.argv) > 3 else 'odoo'
host = sys.argv[4] if len(sys.argv) > 4 else 'db'
port = int(sys.argv[5]) if len(sys.argv) > 5 else 5432

print(f"[{db}] Connecting to {host}:{port}")
conn = psycopg2.connect(dbname=db, user=user, password=pwd, host=host, port=port)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM rule_group_rel WHERE group_id = 118")
count = cur.fetchone()[0]

if count == 0:
    print(f"[{db}] No orphan rows found in rule_group_rel for group_id=118 — nothing to do.")
else:
    cur.execute("DELETE FROM rule_group_rel WHERE group_id = 118")
    conn.commit()
    print(f"[{db}] Deleted {count} orphan row(s) from rule_group_rel where group_id=118.")

conn.close()
