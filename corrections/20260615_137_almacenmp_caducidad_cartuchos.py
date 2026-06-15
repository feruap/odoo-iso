# Activar fecha de caducidad en cartuchos y calcular 4 años desde mes de ingreso
# Formato lote: CLAVE + MM + YY + VV  →  últimos 6 chars antes del final = MMYYVV

from dateutil.relativedelta import relativedelta
from datetime import datetime

# ─── 1. Activar use_expiration_date en todos los cartuchos ───────────────────
cartuchos = env['product.template'].search([
    '|',
    ('name', 'ilike', 'cartucho'),
    ('default_code', 'ilike', 'MPCAC'),
])
cartuchos.write({'use_expiration_date': True})
print("use_expiration_date activado en %d productos" % len(cartuchos))

# ─── 2. Calcular y asignar fecha de caducidad a cada lote ───────────────────
lotes_car = env['stock.lot'].search([
    ('product_id.default_code', 'like', 'CAR')
])
lotes_cac = env['stock.lot'].search([
    ('product_id.default_code', 'like', 'MPCAC')
])
lotes = lotes_car | lotes_cac

ok = 0
errores = []

for l in lotes:
    nombre = l.name
    try:
        mm = int(nombre[-6:-4])
        yy = int(nombre[-4:-2])
        fecha_entrada = datetime(2000 + yy, mm, 1)
        fecha_cad = fecha_entrada + relativedelta(years=4)
        l.write({'expiration_date': fecha_cad})
        ok += 1
    except Exception as e:
        errores.append("%s: %s" % (nombre, e))

print("Lotes actualizados: %d" % ok)
if errores:
    print("Errores: %s" % errores)

# ─── 3. Verificar muestra ────────────────────────────────────────────────────
muestra = env['stock.lot'].search([
    ('product_id.default_code', 'in', ['CAR69', 'CAR70', 'MPCAC06'])
], limit=5)
# Buscar por nombre en cambio
muestra2 = env['stock.lot'].search([
    ('name', 'in', ['CAR69062201', 'CAR70062202', 'CAC06032601', 'CAC06122401'])
])
print("\n=== Verificación ===")
for l in muestra2:
    print("  %s → caducidad: %s" % (l.name, l.expiration_date))

env.cr.commit()
print("\nCOMMIT OK")
