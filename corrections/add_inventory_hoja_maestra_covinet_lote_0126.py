"""
add_inventory_hoja_maestra_covinet_lote_0126.py

Agrega inventario del producto "Hoja maestra covinet Ag" en la ubicación AMP/Existencias.
Crea (o actualiza si ya existe) los siguientes registros:
  - amunet.lot.factory  : HMC01012601
  - stock.lot           : 0126/01/CON  (vinculado al factory lot)
  - stock.quant         : 1680 unidades en AMP/Existencias

Datos del lote:
  - Número de lote (stock.lot.name)     : 0126/01/CON
  - Lote fábrica (factory_lot_id.name)  : HMC01012601
  - Fecha de caducidad                  : 2028-01-31
  - Fecha de remoción                   : 2027-12-30
  - Cantidad                            : 1680

Uso:
    python3 add_inventory_hoja_maestra_covinet_lote_0126.py DB_NAME DB_USER DB_PASSWORD DB_HOST DB_PORT
"""
import sys
from datetime import datetime, timezone

try:
    import psycopg2
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psycopg2-binary', '-q'])
    import psycopg2

# ---------------------------------------------------------------------------
# Parámetros de conexión
# ---------------------------------------------------------------------------
db   = sys.argv[1] if len(sys.argv) > 1 else 'Amunet_testing'
user = sys.argv[2] if len(sys.argv) > 2 else 'odoo'
pwd  = sys.argv[3] if len(sys.argv) > 3 else 'odoo'
host = sys.argv[4] if len(sys.argv) > 4 else 'db'
port = sys.argv[5] if len(sys.argv) > 5 else '5432'

# ---------------------------------------------------------------------------
# Constantes del ajuste
# ---------------------------------------------------------------------------
LOT_NAME          = '0126/01/CON'
FACTORY_LOT_NAME  = 'HMC01012601'
PRODUCT_NAME      = 'Hoja maestra covinet Ag'
LOCATION_SEARCH   = 'AMP%Existencias'   # LIKE pattern para complete_name
EXPIRATION_DATE   = '2028-01-31 23:59:59+00'
REMOVAL_DATE      = '2027-12-30 23:59:59+00'
QUANTITY          = 1680.0

# ---------------------------------------------------------------------------
print(f"[INFO] Conectando a '{db}' en {host}:{port} como '{user}'...")
conn = psycopg2.connect(dbname=db, user=user, password=pwd, host=host, port=port)
cur  = conn.cursor()

# ---------------------------------------------------------------------------
# 1. Obtener company_id (primera compañía disponible)
# ---------------------------------------------------------------------------
cur.execute("SELECT id FROM res_company ORDER BY id LIMIT 1;")
row = cur.fetchone()
if not row:
    print("[ERROR] No se encontró ninguna compañía en la base de datos.")
    sys.exit(1)
company_id = row[0]
print(f"[OK]   company_id = {company_id}")

# ---------------------------------------------------------------------------
# 2. Buscar producto "Hoja maestra covinet Ag"
#    En Odoo 17 el campo name de product_template es JSONB traducible.
#    Buscamos por coincidencia parcial en el texto del JSONB.
# ---------------------------------------------------------------------------
cur.execute("""
    SELECT pp.id
    FROM product_product pp
    JOIN product_template pt ON pt.id = pp.product_tmpl_id
    WHERE pt.name::text ILIKE %s
    LIMIT 1;
""", (f'%{PRODUCT_NAME}%',))
row = cur.fetchone()
if not row:
    print(f"[ERROR] Producto '{PRODUCT_NAME}' no encontrado.")
    conn.close()
    sys.exit(1)
product_id = row[0]
print(f"[OK]   product_id = {product_id} ('{PRODUCT_NAME}')")

# ---------------------------------------------------------------------------
# 3. Buscar ubicación AMP/Existencias
#    complete_name es un campo almacenado que contiene la ruta completa.
#    Filtramos por usage='internal' para evitar ubicaciones virtuales.
# ---------------------------------------------------------------------------
cur.execute("""
    SELECT id, complete_name
    FROM stock_location
    WHERE complete_name ILIKE %s
      AND usage = 'internal'
    ORDER BY id
    LIMIT 1;
""", (f'%{LOCATION_SEARCH}%',))
row = cur.fetchone()
if not row:
    print(f"[ERROR] Ubicación con patrón '{LOCATION_SEARCH}' no encontrada (usage='internal').")
    conn.close()
    sys.exit(1)
location_id, complete_name = row
print(f"[OK]   location_id = {location_id} ('{complete_name}')")

# ---------------------------------------------------------------------------
# 4. Buscar o crear amunet.lot.factory con name = FACTORY_LOT_NAME
#    Restricción única: unique(name)
# ---------------------------------------------------------------------------
cur.execute("""
    SELECT id FROM amunet_lot_factory
    WHERE name = %s
    LIMIT 1;
""", (FACTORY_LOT_NAME,))
row = cur.fetchone()
if row:
    factory_lot_id = row[0]
    print(f"[OK]   amunet.lot.factory ya existe: id={factory_lot_id} ('{FACTORY_LOT_NAME}')")
else:
    cur.execute("""
        INSERT INTO amunet_lot_factory (name, create_uid, write_uid, create_date, write_date)
        VALUES (%s, 1, 1, NOW(), NOW())
        RETURNING id;
    """, (FACTORY_LOT_NAME,))
    factory_lot_id = cur.fetchone()[0]
    print(f"[CREADO] amunet.lot.factory: id={factory_lot_id} ('{FACTORY_LOT_NAME}')")

# ---------------------------------------------------------------------------
# 5. Buscar o crear stock.lot con name = LOT_NAME para el producto
#    Restricción única estándar de Odoo: unique(name, product_id, company_id)
# ---------------------------------------------------------------------------
cur.execute("""
    SELECT id FROM stock_lot
    WHERE name = %s
      AND product_id = %s
      AND company_id = %s
    LIMIT 1;
""", (LOT_NAME, product_id, company_id))
row = cur.fetchone()
if row:
    lot_id = row[0]
    # Actualizar campos personalizados y fechas en caso de que difieran
    cur.execute("""
        UPDATE stock_lot
        SET factory_lot_id   = %s,
            expiration_date  = %s,
            removal_date     = %s,
            write_date       = NOW()
        WHERE id = %s;
    """, (factory_lot_id, EXPIRATION_DATE, REMOVAL_DATE, lot_id))
    print(f"[ACTUALIZADO] stock.lot: id={lot_id} ('{LOT_NAME}') — factory_lot, fechas actualizadas")
else:
    cur.execute("""
        INSERT INTO stock_lot (
            name, product_id, company_id,
            factory_lot_id,
            expiration_date, removal_date,
            create_uid, write_uid, create_date, write_date
        )
        VALUES (%s, %s, %s, %s, %s, %s, 1, 1, NOW(), NOW())
        RETURNING id;
    """, (LOT_NAME, product_id, company_id,
          factory_lot_id,
          EXPIRATION_DATE, REMOVAL_DATE))
    lot_id = cur.fetchone()[0]
    print(f"[CREADO] stock.lot: id={lot_id} ('{LOT_NAME}')")

# ---------------------------------------------------------------------------
# 6. Buscar o crear/actualizar stock.quant
#    Clave única: (product_id, location_id, lot_id, package_id, owner_id)
#    Sin package ni owner → (product_id, location_id, lot_id) es suficiente.
# ---------------------------------------------------------------------------
cur.execute("""
    SELECT id, quantity
    FROM stock_quant
    WHERE product_id  = %s
      AND location_id = %s
      AND lot_id      = %s
      AND (package_id IS NULL)
      AND (owner_id   IS NULL)
    LIMIT 1;
""", (product_id, location_id, lot_id))
row = cur.fetchone()
if row:
    quant_id, current_qty = row
    cur.execute("""
        UPDATE stock_quant
        SET quantity   = %s,
            write_date = NOW()
        WHERE id = %s;
    """, (QUANTITY, quant_id))
    print(f"[ACTUALIZADO] stock.quant: id={quant_id} — cantidad {current_qty} → {QUANTITY}")
else:
    cur.execute("""
        INSERT INTO stock_quant (
            product_id, company_id, location_id, lot_id,
            quantity, reserved_quantity,
            in_date,
            create_uid, write_uid, create_date, write_date
        )
        VALUES (%s, %s, %s, %s, %s, 0, NOW(), 1, 1, NOW(), NOW())
        RETURNING id;
    """, (product_id, company_id, location_id, lot_id, QUANTITY))
    quant_id = cur.fetchone()[0]
    print(f"[CREADO] stock.quant: id={quant_id} — cantidad={QUANTITY} en location_id={location_id}")

# ---------------------------------------------------------------------------
conn.commit()
conn.close()
print(f"\n[LISTO] Ajuste de inventario aplicado correctamente en '{db}'.")
