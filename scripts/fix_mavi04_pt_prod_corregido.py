"""
CORRECCIÓN MAVI-04 para todos los PT en PRODUCCIÓN (amunet_prod)
=================================================================
Cambios:
  1. Crea 4 specs nuevas diferenciadas (si no existen):
       Rasgaduras — Empaque  (seq 30)
       Deformidad o deterioro — Empaque  (seq 40)
       Rasgaduras — Prueba   (seq 60)
       Deformidad o deterioro — Prueba   (seq 70)

  2. Limpia duplicados de DMDEN01, DMFRT02, DMPSA01, DMTSH02
     (desactiva el rel secundario que tenía 2 configs extra).

  3. Para TODOS los PT (DM/DL/DIAM/DRAM/DEMAM):
       - Cambia spec 691 "Rasgaduras" → "Rasgaduras — Empaque"
       - Cambia spec 692 "Deformidad o deterioro" → "Deformidad o deterioro — Empaque"

  4. Para los 20 productos con solo 3 specs:
       - Agrega Polvo (spec 689, seq 10)
       - Agrega Manchas y/o suciedad (spec 690, seq 20)

  5. Para los 98 productos (74 + 20 + 4 ya limpios):
       - Agrega Rasgaduras — Prueba (seq 60)
       - Agrega Deformidad o deterioro — Prueba (seq 70)

  NO toca Hojas Maestras (SPHMC/SPHMT) ni cartuchos (MPCAR).
  Solo afecta productos cuyo default_code empieza con DM/DL/DIAM/DRAM/DEMAM.

Solicitado por: Diana Flores — Control de Calidad, 2026-09-22
"""

Spec   = env['amunet.quality.check.parameter.specification']
Config = env['amunet.quality.parameter.specification.config']
Param  = env['amunet.quality.check.parameter']
PT     = env['product.template']

PT_PREFIXES = ('DM', 'DL', 'DIAM', 'DRAM', 'DEMAM')
REL_IDS_DUPLICADOS = [4693, 4279, 4285, 4273]   # rel secundarios con Rasgaduras/Deformidad duplicados

mavi04 = Param.browse(145)
assert mavi04.exists() and mavi04.code == 'MAVI-04', "El parametro 145 no es MAVI-04"
# Hay 4 parametros con codigo MAVI-04 (1, 113, 114, 145). Los 94 bloques de PT
# usan el 145 'Aspectos Visuales'. search(limit=1) devolvia otro y dejaba las
# specs colgando de un parametro que ningun PT usa.
print(f"Parámetro MAVI-04: id={mavi04.id}")

# ─────────────────────────────────────────────────────────────────────────────
# PASO 1: Crear specs nuevas si no existen
# ─────────────────────────────────────────────────────────────────────────────
def get_or_create_spec(name, seq):
    s = Spec.search([('name', '=', name), ('parameter_id', '=', mavi04.id),
                     ('evaluation_type', '=', 'binary_selection')], limit=1)
    if not s:
        s = Spec.create({'name': name, 'parameter_id': mavi04.id,
                         'evaluation_type': 'binary_selection', 'sequence': seq, 'active': True})
        print(f"  CREADA spec: '{name}' id={s.id}")
    else:
        print(f"  Ya existe spec: '{name}' id={s.id}")
    return s

spec_ras_emp = get_or_create_spec('Rasgaduras — Empaque', 30)
spec_def_emp = get_or_create_spec('Deformidad o deterioro — Empaque', 40)
spec_ras_pru = get_or_create_spec('Rasgaduras — Prueba', 60)
spec_def_pru = get_or_create_spec('Deformidad o deterioro — Prueba', 70)

spec_polvo   = Spec.browse(689)   # Polvo (ya existe)
spec_manchas = Spec.browse(690)   # Manchas y/o suciedad (ya existe)
spec_ras_old = 691                # ID del spec "Rasgaduras" sin sufijo
spec_def_old = 692                # ID del spec "Deformidad o deterioro" sin sufijo

print(f"\nSpecs de referencia: Polvo={spec_polvo.name}(689), Manchas={spec_manchas.name}(690)")
print(f"Specs nuevas: Empaque=({spec_ras_emp.id},{spec_def_emp.id}), Prueba=({spec_ras_pru.id},{spec_def_pru.id})")

# ─────────────────────────────────────────────────────────────────────────────
# PASO 2: Desactivar configs duplicados (rel secundarios)
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- PASO 2: Limpiar duplicados ---")
dups = Config.search([('product_parameter_rel_id', 'in', REL_IDS_DUPLICADOS), ('active', '=', True)])
print(f"  Desactivando {len(dups)} configs duplicados (rel_ids {REL_IDS_DUPLICADOS})")
dups.write({'active': False})

# ─────────────────────────────────────────────────────────────────────────────
# PASO 3 + 4 + 5: Procesar cada producto PT
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- PASOS 3-5: Procesar productos PT ---")

pt_products = PT.search([
    '|', '|', '|', '|',
    ('default_code', 'ilike', 'DM%'),
    ('default_code', 'ilike', 'DL%'),
    ('default_code', 'ilike', 'DIAM%'),
    ('default_code', 'ilike', 'DRAM%'),
    ('default_code', 'ilike', 'DEMAM%'),
])
pt_products = pt_products.filtered(lambda p: p.default_code and any(
    p.default_code.upper().startswith(pfx) for pfx in PT_PREFIXES
))

stats = {'swap_ras': 0, 'swap_def': 0, 'add_polvo': 0, 'add_manchas': 0,
         'add_ras_pru': 0, 'add_def_pru': 0, 'sin_mavi04': 0}

for pt in pt_products:
    # Obtener configs activos de MAVI-04 para este producto
    configs = Config.search([
        ('product_tmpl_id', '=', pt.id),
        ('parameter_id', '=', mavi04.id),
        ('active', '=', True),
    ])
    if not configs:
        stats['sin_mavi04'] += 1
        continue

    # rel_id canónico: el que tiene más configs activos
    from collections import Counter
    rel_counts = Counter(c.product_parameter_rel_id for c in configs)
    canonical_rel = rel_counts.most_common(1)[0][0].id   # el id, no el recordset

    specs_activos = {c.specification_id.id: c for c in configs
                     if c.product_parameter_rel_id.id == canonical_rel}

    # Obtener product_tmpl_id y parameter_id del primer config para usarlos en INSERT
    sample_cfg = configs.filtered(lambda c: c.product_parameter_rel_id.id == canonical_rel)[0]

    def add_spec(spec, seq):
        if spec.id not in specs_activos:
            Config.create({
                'product_parameter_rel_id': canonical_rel,
                'specification_id': spec.id,
                'product_tmpl_id': pt.id,
                'parameter_id': mavi04.id,
                'evaluation_type': 'binary_selection',
                'sequence': seq,
                'active': True,
            })
            return True
        return False

    # PASO 3: Cambiar Rasgaduras (691) → Empaque
    if spec_ras_old in specs_activos:
        specs_activos[spec_ras_old].write({'specification_id': spec_ras_emp.id})
        stats['swap_ras'] += 1

    # PASO 3: Cambiar Deformidad (692) → Empaque
    if spec_def_old in specs_activos:
        specs_activos[spec_def_old].write({'specification_id': spec_def_emp.id})
        stats['swap_def'] += 1

    # PASO 4: Agregar Polvo si falta
    if add_spec(spec_polvo, 10):
        stats['add_polvo'] += 1

    # PASO 4: Agregar Manchas si falta
    if add_spec(spec_manchas, 20):
        stats['add_manchas'] += 1

    # PASO 5: Agregar Rasgaduras — Prueba si falta
    if add_spec(spec_ras_pru, 60):
        stats['add_ras_pru'] += 1

    # PASO 5: Agregar Deformidad — Prueba si falta
    if add_spec(spec_def_pru, 70):
        stats['add_def_pru'] += 1

print(f"\nRESUMEN:")
print(f"  Rasgaduras  → Empaque:          {stats['swap_ras']} productos")
print(f"  Deformidad  → Empaque:          {stats['swap_def']} productos")
print(f"  Polvo agregado:                 {stats['add_polvo']} productos")
print(f"  Manchas agregadas:              {stats['add_manchas']} productos")
print(f"  Rasgaduras — Prueba agregada:   {stats['add_ras_pru']} productos")
print(f"  Deformidad — Prueba agregada:   {stats['add_def_pru']} productos")
print(f"  Sin MAVI-04 (skip):             {stats['sin_mavi04']} productos")

env.cr.commit()
print("\n✓ Cambios guardados en producción.")
