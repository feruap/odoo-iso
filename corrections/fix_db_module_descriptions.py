"""
Fix ir.module.module description text in DB that causes docutils RST crash.
Replaces the problematic JSONB description values with simplified versions
for all amunet_* modules.

Usage: python3 /tmp/fix_db_desc.py DB_NAME DB_USER DB_PASSWORD DB_HOST DB_PORT
"""
import sys
import json

try:
    import psycopg2
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psycopg2-binary', '-q'])
    import psycopg2

db   = sys.argv[1] if len(sys.argv) > 1 else 'amunet_prod'
user = sys.argv[2] if len(sys.argv) > 2 else 'odoo'
pwd  = sys.argv[3] if len(sys.argv) > 3 else 'odoo'
host = sys.argv[4] if len(sys.argv) > 4 else 'db'
port = sys.argv[5] if len(sys.argv) > 5 else '5432'

print(f"Connecting to {db} @ {host}:{port}")
conn = psycopg2.connect(dbname=db, user=user, password=pwd, host=host, port=port)
cur = conn.cursor()

# Simplified one-liner descriptions without RST formatting issues
CLEAN_DESCRIPTIONS = {
    'amunet_lot':                   'Generacion automatica de secuencias de lotes para Odoo.',
    'amunet_quality':               'Sistema de Control de Calidad para manufactura de dispositivos medicos y productos farmaceuticos.',
    'amunet_auditorias':            'Gestion del Programa de Auditorias bajo ISO 13485.',
    'amunet_warehouse_access':      'Control de acceso dinamico por almacen y operaciones de inventario.',
    'amunet_competencias':          'Gestion de capacitacion y competencias para analistas de calidad bajo ISO 13485.',
    'amunet_equipment_calibration': 'Control de calibracion de equipos bajo ISO 13485 Clausula 7.6.',
    'amunet_transfer_bom':          'Transferencia y gestion de listas de materiales.',
}

fixed = 0
for module_name, clean_desc in CLEAN_DESCRIPTIONS.items():
    # Get current description
    cur.execute("SELECT id, description FROM ir_module_module WHERE name = %s", (module_name,))
    row = cur.fetchone()
    if not row:
        print(f"  {module_name}: not installed, skip")
        continue
    
    module_id, current_desc = row
    if not current_desc:
        print(f"  {module_name}: no description, skip")
        continue
    
    # Build new simplifed JSONB with same language keys but clean text
    try:
        desc_dict = current_desc
        if isinstance(desc_dict, str):
            desc_dict = json.loads(desc_dict)
        
        new_desc = {lang: clean_desc for lang in desc_dict.keys()}
    except Exception:
        new_desc = {'en_US': clean_desc, 'es_MX': clean_desc}
    
    cur.execute(
        "UPDATE ir_module_module SET description = %s WHERE id = %s",
        (json.dumps(new_desc), module_id)
    )
    print(f"  [FIXED] {module_name}: description cleaned for {list(new_desc.keys())}")
    fixed += 1

conn.commit()
conn.close()
print(f"\nDone. Fixed {fixed} module descriptions in {db}.")
