# Revertir scripts 129 y 131 — dejar solicitudes de material como estaban

karla_id   = 78
veronica_id = 62

# ─── 1. Revertir jerarquía (script 131) ──────────────────────────────────────
# Quitar entradas correctas que agregué
wrong_to_delete = [(132, 131), (131, 130), (145, 130)]
for hid, gid in wrong_to_delete:
    env.cr.execute("DELETE FROM res_groups_implied_rel WHERE hid=%s AND gid=%s", (hid, gid))
    print("DELETE hid=%d→gid=%d: %d filas" % (hid, gid, env.cr.rowcount))

# Restaurar entradas originales
original = [(131, 132), (130, 131)]
for hid, gid in original:
    env.cr.execute(
        "INSERT INTO res_groups_implied_rel (hid, gid) VALUES (%s, %s) ON CONFLICT DO NOTHING",
        (hid, gid)
    )
    print("RESTORE hid=%d→gid=%d: %d filas" % (hid, gid, env.cr.rowcount))

# ─── 2. Revertir roles de Karla (script 129) ─────────────────────────────────
karla = env['res.users'].browse(karla_id)
karla.write({
    'amunet_material_requires_head_approval': False,
    'amunet_material_head_id': False,
})
print("Karla: aprobación de jefe = False, jefa = ninguna")

# Devolver a Karla al grupo Almacén (131)
env.cr.execute(
    "INSERT INTO res_groups_users_rel (gid, uid) VALUES (131, %s) ON CONFLICT DO NOTHING",
    (karla_id,)
)
print("Karla: devuelta al grupo Almacén(131): %d filas" % env.cr.rowcount)

# ─── 3. Verificar estado final ────────────────────────────────────────────────
env.cr.execute("""
    SELECT ir.hid, ir.gid, pg.name::text, cg.name::text
    FROM res_groups_implied_rel ir
    JOIN res_groups pg ON pg.id = ir.hid
    JOIN res_groups cg ON cg.id = ir.gid
    WHERE ir.hid IN (130,131,132,145) OR ir.gid IN (130,131,132,145)
    ORDER BY ir.hid, ir.gid
""")
print("\n=== Jerarquía restaurada ===")
for r in env.cr.fetchall():
    print("  hid=%d(%s) → gid=%d(%s)" % (r[0], r[2], r[1], r[3]))

env.cr.execute("""
    SELECT rel.uid, rg.id, rg.name::text
    FROM res_groups_users_rel rel
    JOIN res_groups rg ON rg.id = rel.gid
    WHERE rel.uid IN (%s, %s) AND rel.gid IN (130,131,132,145)
    ORDER BY rel.uid, rg.id
""", (karla_id, veronica_id))
print("\n=== Membresías restauradas ===")
for r in env.cr.fetchall():
    print("  uid=%d: gid=%d %s" % (r[0], r[1], r[2]))

env.cr.commit()
print("\nCOMMIT OK — revert completo")
