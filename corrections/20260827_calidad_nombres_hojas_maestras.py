"""
Corrección: nombres de hojas maestras SPHMC77/78/79/85/86/87/88
y archivado de SPHMC81/82/83/84 (no deben existir).
Confirmado por Diana Flores, 2026-08-27.

Idempotente — seguro de correr más de una vez.
Correr UNA VEZ después del deploy a producción.
"""

# ── Nombres SPHMC77 / 78 / 79 ───────────────────────────────────────────────
env.cr.execute("""
    UPDATE product_template
    SET name = jsonb_build_object('es_MX', 'Hoja Maestra Transglutaminasa IgA'),
        write_date = NOW()
    WHERE default_code = 'SPHMC77'
      AND (name IS NULL OR name->>'es_MX' IS NULL OR name->>'es_MX' = '')
""")
print("SPHMC77 → 'Hoja Maestra Transglutaminasa IgA'")

env.cr.execute("""
    UPDATE product_template
    SET name = jsonb_build_object('es_MX', 'Hoja Maestra HPV E7'),
        write_date = NOW()
    WHERE default_code = 'SPHMC78'
      AND (name IS NULL OR name->>'es_MX' IS NULL OR name->>'es_MX' = '')
""")
print("SPHMC78 → 'Hoja Maestra HPV E7'")

env.cr.execute("""
    UPDATE product_template
    SET name = jsonb_build_object('es_MX', 'Hoja Maestra CARBA 5 en 1'),
        write_date = NOW()
    WHERE default_code = 'SPHMC79'
      AND (name IS NULL OR name->>'es_MX' IS NULL OR name->>'es_MX' = '')
""")
print("SPHMC79 → 'Hoja Maestra CARBA 5 en 1'")

# ── Nombres SPHMC85 / 86 / 87 / 88 ─────────────────────────────────────────
env.cr.execute("""
    UPDATE product_template
    SET name = jsonb_build_object('es_MX', 'Hoja Maestra Dengue IgG/IgM CM'),
        write_date = NOW()
    WHERE default_code = 'SPHMC85'
      AND (name IS NULL OR name->>'es_MX' IS NULL OR name->>'es_MX' = '')
""")
print("SPHMC85 → 'Hoja Maestra Dengue IgG/IgM CM'")

env.cr.execute("""
    UPDATE product_template
    SET name = jsonb_build_object('es_MX', 'Hoja Maestra Zika IgG/IgM CM'),
        write_date = NOW()
    WHERE default_code = 'SPHMC86'
      AND (name IS NULL OR name->>'es_MX' IS NULL OR name->>'es_MX' = '')
""")
print("SPHMC86 → 'Hoja Maestra Zika IgG/IgM CM'")

env.cr.execute("""
    UPDATE product_template
    SET name = jsonb_build_object('es_MX', 'Hoja Maestra Chikungunya IgG CM'),
        write_date = NOW()
    WHERE default_code = 'SPHMC87'
      AND (name IS NULL OR name->>'es_MX' IS NULL OR name->>'es_MX' = '')
""")
print("SPHMC87 → 'Hoja Maestra Chikungunya IgG CM'")

env.cr.execute("""
    UPDATE product_template
    SET name = jsonb_build_object('es_MX', 'Hoja Maestra Chikungunya IgM CM'),
        write_date = NOW()
    WHERE default_code = 'SPHMC88'
      AND (name IS NULL OR name->>'es_MX' IS NULL OR name->>'es_MX' = '')
""")
print("SPHMC88 → 'Hoja Maestra Chikungunya IgM CM'")

# ── Archivar SPHMC81/82/83/84 (no deben existir; conserva historial) ────────
env.cr.execute("""
    UPDATE product_template SET active = false, write_date = NOW()
    WHERE default_code IN ('SPHMC81','SPHMC82','SPHMC83','SPHMC84')
      AND active = true
""")
env.cr.execute("""
    UPDATE product_product SET active = false, write_date = NOW()
    WHERE product_tmpl_id IN (
        SELECT id FROM product_template
        WHERE default_code IN ('SPHMC81','SPHMC82','SPHMC83','SPHMC84')
    ) AND active = true
""")
print("SPHMC81/82/83/84 → archivados (active=false)")

print("\n✓ Script completado.")
