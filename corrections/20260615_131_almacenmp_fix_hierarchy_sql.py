# Diagnóstico y corrección directa vía SQL de la jerarquía de grupos
# El script 130 (ORM) no corrigió la tabla — usamos SQL directo.

g_ids = [130, 131, 132, 145]  # requester, warehouse, manager, dept_head
karla_id = 78
veronica_id = 62

# ─── 1. Estado actual de implied_ids (directas) ──────────────────────────────
env.cr.execute("""
    SELECT ir.hid, ir.gid,
           pg.name::text, cg.name::text
    FROM res_groups_implied_rel ir
    JOIN res_groups pg ON pg.id = ir.hid
    JOIN res_groups cg ON cg.id = ir.gid
    WHERE ir.hid = ANY(%s) OR ir.gid = ANY(%s)
    ORDER BY ir.hid, ir.gid
""", (g_ids, g_ids))
print("=== implied_ids ANTES ===")
rows_before = env.cr.fetchall()
for r in rows_before:
    print("  hid=%d(%s) → gid=%d(%s)" % (r[0], r[2], r[1], r[3]))

# ─── 2. Membresías directas de Karla y Verónica en grupos de material ────────
env.cr.execute("""
    SELECT rel.uid, rg.id, rg.name::text
    FROM res_groups_users_rel rel
    JOIN res_groups rg ON rg.id = rel.gid
    WHERE rel.uid IN (%s, %s) AND rel.gid = ANY(%s)
    ORDER BY rel.uid, rg.id
""", (karla_id, veronica_id, g_ids))
print("\n=== Membresías en grupos de material ===")
for r in env.cr.fetchall():
    user_name = "Karla(78)" if r[0] == karla_id else "Veronica(62)"
    print("  %s: gid=%d %s" % (user_name, r[1], r[2]))

# ─── 3. Corrección SQL de implied_ids ────────────────────────────────────────
# Entradas INCORRECTAS que deben eliminarse:
wrong_pairs = [
    (131, 132),   # Almacén → Administrador  (INVERTED)
    (130, 131),   # Solicitante → Almacén    (INVERTED)
    (130, 132),   # Solicitante → Administrador (transitive del error)
]
for hid, gid in wrong_pairs:
    env.cr.execute(
        "DELETE FROM res_groups_implied_rel WHERE hid=%s AND gid=%s",
        (hid, gid)
    )
    print("DELETE hid=%d→gid=%d: %d filas" % (hid, gid, env.cr.rowcount))

# Entradas CORRECTAS que deben existir (solo directas, según XML):
correct_pairs = [
    (132, 131),   # Administrador → Almacén
    (131, 130),   # Almacén → Solicitante
    (145, 130),   # Jefe de área → Solicitante
    # (131, stock_user_id) — lo agrega Odoo al actualizar, no necesitamos forzarlo
]
for hid, gid in correct_pairs:
    env.cr.execute("""
        INSERT INTO res_groups_implied_rel (hid, gid)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
    """, (hid, gid))
    print("INSERT hid=%d→gid=%d: %d filas" % (hid, gid, env.cr.rowcount))

# ─── 4. Corregir membresías directas de Verónica ─────────────────────────────
# Si el implied_ids estaba invertido cuando la agregaron a Almacén,
# Odoo pudo haberla añadido también a Administrador automáticamente.
env.cr.execute(
    "DELETE FROM res_groups_users_rel WHERE gid=132 AND uid=%s",
    (veronica_id,)
)
print("\nVerónica quitada de Administrador(132): %d filas" % env.cr.rowcount)

# Asegurar que Verónica SÍ tiene Almacén (131)
env.cr.execute("""
    INSERT INTO res_groups_users_rel (gid, uid)
    VALUES (131, %s)
    ON CONFLICT DO NOTHING
""", (veronica_id,))
print("Verónica en Almacén(131): %d filas insertadas" % env.cr.rowcount)

# Asegurar que Karla tiene Solicitante (130) pero NO Almacén (131)
env.cr.execute(
    "DELETE FROM res_groups_users_rel WHERE gid=131 AND uid=%s",
    (karla_id,)
)
print("Karla quitada de Almacén(131): %d filas" % env.cr.rowcount)

env.cr.execute("""
    INSERT INTO res_groups_users_rel (gid, uid)
    VALUES (130, %s)
    ON CONFLICT DO NOTHING
""", (karla_id,))
print("Karla en Solicitante(130): %d filas insertadas" % env.cr.rowcount)

# ─── 5. Estado final ──────────────────────────────────────────────────────────
env.cr.execute("""
    SELECT ir.hid, ir.gid,
           pg.name::text, cg.name::text
    FROM res_groups_implied_rel ir
    JOIN res_groups pg ON pg.id = ir.hid
    JOIN res_groups cg ON cg.id = ir.gid
    WHERE ir.hid = ANY(%s) OR ir.gid = ANY(%s)
    ORDER BY ir.hid, ir.gid
""", (g_ids, g_ids))
print("\n=== implied_ids DESPUÉS ===")
for r in env.cr.fetchall():
    print("  hid=%d(%s) → gid=%d(%s)" % (r[0], r[2], r[1], r[3]))

env.cr.execute("""
    SELECT rel.uid, rg.id, rg.name::text
    FROM res_groups_users_rel rel
    JOIN res_groups rg ON rg.id = rel.gid
    WHERE rel.uid IN (%s, %s) AND rel.gid = ANY(%s)
    ORDER BY rel.uid, rg.id
""", (karla_id, veronica_id, g_ids))
print("\n=== Membresías DESPUÉS ===")
for r in env.cr.fetchall():
    user_name = "Karla(78)" if r[0] == karla_id else "Veronica(62)"
    print("  %s: gid=%d %s" % (user_name, r[1], r[2]))

env.cr.commit()
print("\nCOMMIT OK")
