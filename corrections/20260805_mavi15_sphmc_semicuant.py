"""
Crea el parametro MAVI-15 y lo asigna a SPHMC25 (Ferritina),
SPHMC38 (PSA semicuantitativa) y SPHMC52 (TSH semicuantitativa),
sustituyendo MAVI-16 en esos 3 productos.

MAVI-16 queda exclusivamente para pruebas colorimetricas:
  Hemoglobina, Vitamina D, Albumina semi, AMH, Alcohol, pH vaginal,
  Infecciones urinarias.

Las spec_configs ya usan mavi_15_ternary como evaluation_type,
solo cambia el codigo del parametro en el catalogo y en los rels.

Confirmado por Diana Flores, 2026-08-05.
Idempotente — seguro de correr mas de una vez.
Correr UNA VEZ despues del deploy a produccion.
"""
Param    = env['amunet.quality.check.parameter']

# ── 1. Crear (o verificar) MAVI-15 en el catalogo ────────────────────────────
mavi15 = Param.search([('code', '=', 'MAVI-15')], limit=1)
if not mavi15:
    mavi15 = Param.create({
        'code': 'MAVI-15',
        'name': 'Visualizacion de lineas semicuantitativas',
    })
    print(f"MAVI-15 creado (id={mavi15.id})")
else:
    print(f"MAVI-15 ya existe (id={mavi15.id}), OK")

env.flush_all()

# ── 2. Actualizar los 3 rels de MAVI-16 a MAVI-15 ────────────────────────────
# SPHMC25=rel 934, SPHMC38=rel 948, SPHMC52=rel 481
REL_IDS = [934, 948, 481]

env.cr.execute("""
    UPDATE amunet_quality_parameter_product_rel
    SET parameter_id   = %s,
        parameter_code = 'MAVI-15',
        parameter_name = 'Visualizacion de lineas semicuantitativas',
        write_date     = NOW()
    WHERE id = ANY(%s)
""", (mavi15.id, REL_IDS))
print(f"Rels actualizados: {env.cr.rowcount} -> MAVI-15")

env.cr.execute("""
    SELECT pp.default_code, rel.parameter_code, rel.parameter_name
    FROM amunet_quality_parameter_product_rel rel
    JOIN product_template pt ON pt.id = rel.product_tmpl_id
    JOIN product_product pp ON pp.product_tmpl_id = pt.id
    WHERE rel.id = ANY(%s)
""", (REL_IDS,))
for row in env.cr.fetchall():
    print(f"  {row[0]}: {row[1]} - {row[2]}")

env.cr.commit()
print("LISTO - MAVI-15 asignado a Ferritina, PSA semi y TSH semi.")
