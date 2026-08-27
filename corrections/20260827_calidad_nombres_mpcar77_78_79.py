"""
Corrección: nombres de cartuchos MPCAR77, MPCAR78 y MPCAR79 en producción.
Confirmado por Diana Flores, 2026-08-27.

Estos productos fueron dados de alta sin nombre; esta corrección los asigna.
Idempotente — seguro de correr más de una vez.
Correr UNA VEZ después del deploy a producción.
"""

# ── MPCAR77 — Cartucho Transglutaminasa IgA (Anti-tTG) ─────────────────────
env.cr.execute("""
    UPDATE product_template
    SET name = jsonb_build_object('es_MX', 'Cartucho Transglutaminasa IgA (Anti-tTG)'),
        write_date = NOW()
    WHERE default_code = 'MPCAR77'
      AND (name IS NULL OR name->>'es_MX' IS NULL OR name->>'es_MX' = '')
""")
print("MPCAR77: nombre → 'Cartucho Transglutaminasa IgA (Anti-tTG)'")

# ── MPCAR78 — Cartucho HPV E7 ───────────────────────────────────────────────
env.cr.execute("""
    UPDATE product_template
    SET name = jsonb_build_object('es_MX', 'Cartucho HPV E7'),
        write_date = NOW()
    WHERE default_code = 'MPCAR78'
      AND (name IS NULL OR name->>'es_MX' IS NULL OR name->>'es_MX' = '')
""")
print("MPCAR78: nombre → 'Cartucho HPV E7'")

# ── MPCAR79 — Cartucho CARBA 5 en 1 ────────────────────────────────────────
env.cr.execute("""
    UPDATE product_template
    SET name = jsonb_build_object('es_MX', 'Cartucho CARBA 5 en 1'),
        write_date = NOW()
    WHERE default_code = 'MPCAR79'
      AND (name IS NULL OR name->>'es_MX' IS NULL OR name->>'es_MX' = '')
""")
print("MPCAR79: nombre → 'Cartucho CARBA 5 en 1'")

print("\n✓ Script completado.")
