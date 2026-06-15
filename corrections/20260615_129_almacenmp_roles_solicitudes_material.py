# Separar roles en Solicitudes de Material: Karla = solicitante, Verónica = almacenista/aprobadora
# Solicitud de Karla (almacen.mp) — 2026-06-15
#
# Cambios:
#  1. Karla requiere aprobación de jefe -> sus solicitudes pasan siempre por Verónica
#  2. Verónica se asigna como jefa de Karla en el módulo
#  3. Karla sale del grupo "Solicitudes de Material / Almacen"
#     -> ya no ve "Iniciar Surtido" ni "Confirmar Entrega"
#  4. Verónica conserva ese grupo -> sigue viendo todos los botones de almacén

karla = env['res.users'].browse(78)
veronica = env['res.users'].browse(62)
grupo_almacen = env['res.groups'].browse(131)   # group_material_warehouse

# --- 1. Activar aprobación obligatoria para Karla y asignar a Verónica como jefa ---
karla.write({
    'amunet_material_requires_head_approval': True,
    'amunet_material_head_id': veronica.id,
})
print("Karla: aprobación de jefe = True, jefa = " + veronica.name)

# --- 2. Quitar a Karla del grupo Almacén usando la tabla de relación directa ---
env.cr.execute(
    "SELECT 1 FROM res_groups_users_rel WHERE gid=%s AND uid=%s",
    (grupo_almacen.id, karla.id)
)
karla_tiene_grupo = bool(env.cr.fetchone())

if karla_tiene_grupo:
    env.cr.execute(
        "DELETE FROM res_groups_users_rel WHERE gid=%s AND uid=%s",
        (grupo_almacen.id, karla.id)
    )
    print("Karla: quitada del grupo Almacén")
else:
    print("Karla: ya no tenía el grupo Almacén (sin cambio)")

# --- 3. Verificar que Verónica sí conserva el grupo ---
env.cr.execute(
    "SELECT 1 FROM res_groups_users_rel WHERE gid=%s AND uid=%s",
    (grupo_almacen.id, veronica.id)
)
veronica_tiene_grupo = bool(env.cr.fetchone())

if veronica_tiene_grupo:
    print("Verónica: conserva grupo Almacén ✓")
else:
    print("AVISO: Verónica no tenía el grupo Almacén — agregándola")
    env.cr.execute(
        "INSERT INTO res_groups_users_rel (gid, uid) VALUES (%s, %s)",
        (grupo_almacen.id, veronica.id)
    )

# --- Resumen ---
env.cr.execute(
    "SELECT ig.name::text FROM res_groups ig JOIN res_groups_users_rel rel ON rel.gid=ig.id WHERE rel.uid=%s AND ig.name::text ILIKE '%%aterial%%'",
    (karla.id,)
)
print("Karla grupos material: " + str([r[0] for r in env.cr.fetchall()]))

env.cr.execute(
    "SELECT ig.name::text FROM res_groups ig JOIN res_groups_users_rel rel ON rel.gid=ig.id WHERE rel.uid=%s AND ig.name::text ILIKE '%%aterial%%'",
    (veronica.id,)
)
print("Verónica grupos material: " + str([r[0] for r in env.cr.fetchall()]))
print("Karla requires_head_approval: " + str(karla.amunet_material_requires_head_approval))
print("Karla head: " + str(karla.amunet_material_head_id.name))

env.cr.commit()
print("COMMIT OK")
