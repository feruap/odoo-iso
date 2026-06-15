# Corregir jerarquía de grupos de amunet_material_request
# Problema: la BD tiene la jerarquía invertida — Almacén implica Administrador
# en lugar de Administrador implicar Almacén. Resultado: Verónica (Almacén)
# aparece como Administradora y ve todos los botones.
#
# Jerarquía CORRECTA (del XML):
#   Administrador → Almacén → Solicitante → Role/Member
#   Jefe de área  → Solicitante
#   Role/Member   → Solicitante   (todos los usuarios pueden solicitar)

def get_group(xml_id):
    return env.ref('amunet_material_request.' + xml_id)

g_requester  = get_group('group_material_requester')   # Solicitante
g_warehouse  = get_group('group_material_warehouse')   # Almacén
g_dept_head  = get_group('group_material_dept_head')   # Jefe de área
g_manager    = get_group('group_material_manager')     # Administrador
g_base_user  = env.ref('base.group_user')              # Role/Member
g_stock_user = env.ref('stock.group_stock_user')       # Stock / User

print("IDs: requester=%d, warehouse=%d, dept_head=%d, manager=%d" % (
    g_requester.id, g_warehouse.id, g_dept_head.id, g_manager.id))

# Resetear cada grupo con (6, 0, [...]) para reemplazar implied_ids completos
g_requester.write({'implied_ids': [(6, 0, [g_base_user.id])]})
print("Solicitante → [Role/Member]")

g_warehouse.write({'implied_ids': [(6, 0, [g_requester.id, g_stock_user.id])]})
print("Almacén → [Solicitante, Stock/User]")

g_dept_head.write({'implied_ids': [(6, 0, [g_requester.id])]})
print("Jefe de área → [Solicitante]")

g_manager.write({'implied_ids': [(6, 0, [g_warehouse.id])]})
print("Administrador → [Almacén]")

# Verificar resultado
env.cr.execute("""
    SELECT parent.name::text AS implica, child.name::text AS implicado
    FROM res_groups_implied_rel ir
    JOIN res_groups parent ON parent.id = ir.hid
    JOIN res_groups child  ON child.id  = ir.gid
    WHERE parent.name::text ILIKE '%%aterial%%'
       OR child.name::text  ILIKE '%%aterial%%'
    ORDER BY parent.name::text
""")
print("--- Jerarquía resultante ---")
for row in env.cr.fetchall():
    print("  " + row[0] + " → " + row[1])

env.cr.commit()
print("COMMIT OK")
