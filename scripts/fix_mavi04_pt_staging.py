"""
CORRECCIÓN MAVI-04 para todos los PT en STAGING (Amunet_testing)
=================================================================
Cambios:
  1. Crea 4 specs nuevas diferenciadas (si no existen):
       Rasgaduras — Empaque  (seq 30)
       Deformidad o deterioro — Empaque  (seq 40)
       Rasgaduras — Prueba   (seq 60)
       Deformidad o deterioro — Prueba   (seq 70)

  2. Limpia duplicados de DMFRT02, DMPSA01, DMTSH02
     (desactiva rel secundarios: 4458, 4470, 4464).

  3. Para TODOS los PT (DM/DL/DIAM/DRAM/DEMAM):
       - Cambia spec 691 "Rasgaduras" → "Rasgaduras — Empaque"
       - Cambia spec 692 "Deformidad o deterioro" → "Deformidad o deterioro — Empaque"

  4. Para todos los PT: agrega Rasgaduras — Prueba (seq 60) y
     Deformidad o deterioro — Prueba (seq 70) si no existen.

  (Polvo y Manchas ya los tienen todos en staging — no se agregan.)

Solicitado por: Diana Flores — Control de Calidad, 2026-09-22
"""

Spec   = env['amunet.quality.check.parameter.specification']
Config = env['amunet.quality.parameter.specification.config']
Param  = env['amunet.quality.check.parameter']
PT     = env['product.template']

PT_PREFIXES = ('DM', 'DL', 'DIAM', 'DRAM', 'DEMAM')
# No hay duplicados para parameter_id=145 en staging; los rel secundarios eran del parámetro viejo
REL_IDS_DUPLICADOS = []

# En staging hay 4 parámetros con code MAVI-04; el correcto para PT es "Aspectos Visuales" (id=145)
mavi04 = Param.search([('code', '=', 'MAVI-04'), ('name', '=', 'Aspectos Visuales')], limit=1)
if not mavi04:
    mavi04 = Param.search([('code', '=', 'MAVI-04')], limit=1)
assert mavi04, "No se encontró el parámetro MAVI-04"
print(f"Parámetro MAVI-04: id={mavi04.id} — {mavi04.name}")

# ─────────────────────────────────────────────────────────────────────────────
# PASO 1: Crear specs nuevas si no existen
# ─────────────────────────────────────────────────────────────────────────────
def get_or_create_spec(name, seq):
    s = Spec.search([('name', '=', name), ('evaluation_type', '=', 'binary_selection')], limit=1)
    if not s:
        s = Spec.create({
            'name': name,
            'evaluation_type': 'binary_selection',
            'sequence': seq,
            'active': True,
            'parameter_id': mavi04.id,
        })
        print(f"  CREADA spec: '{name}' id={s.id}")
    else:
        print(f"  Ya existe spec: '{name}' id={s.id}")
    return s

spec_ras_emp = get_or_create_spec('Rasgaduras — Empaque', 30)
spec_def_emp = get_or_create_spec('Deformidad o deterioro — Empaque', 40)
spec_ras_pru = get_or_create_spec('Rasgaduras — Prueba', 60)
spec_def_pru = get_or_create_spec('Deformidad o deterioro — Prueba', 70)

spec_ras_old = 691   # "Rasgaduras" genérico
spec_def_old = 692   # "Deformidad o deterioro" genérico

print(f"\nSpecs nuevas: Empaque=({spec_ras_emp.id},{spec_def_emp.id}), Prueba=({spec_ras_pru.id},{spec_def_pru.id})")

# ─────────────────────────────────────────────────────────────────────────────
# PASO 2: Desactivar configs duplicados (rel secundarios)
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- PASO 2: Limpiar duplicados ---")
dups = Config.search([('product_parameter_rel_id', 'in', REL_IDS_DUPLICADOS), ('active', '=', True)])
print(f"  Desactivando {len(dups)} configs duplicados (rel_ids {REL_IDS_DUPLICADOS})")
dups.write({'active': False})

# ─────────────────────────────────────────────────────────────────────────────
# PASO 3 + 4: Procesar cada producto PT
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- PASOS 3-4: Procesar productos PT ---")

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

stats = {'swap_ras': 0, 'swap_def': 0, 'add_ras_pru': 0, 'add_def_pru': 0, 'sin_mavi04': 0}

from collections import Counter

for pt in pt_products:
    configs = Config.search([
        ('product_tmpl_id', '=', pt.id),
        ('parameter_id', '=', mavi04.id),
        ('active', '=', True),
    ])
    if not configs:
        stats['sin_mavi04'] += 1
        continue

    rel_counts = Counter(c.product_parameter_rel_id.id for c in configs)
    canonical_rel_id = rel_counts.most_common(1)[0][0]

    specs_activos = {c.specification_id.id: c for c in configs
                     if c.product_parameter_rel_id.id == canonical_rel_id}

    def add_spec(spec, seq):
        if spec.id not in specs_activos:
            Config.create({
                'product_parameter_rel_id': canonical_rel_id,
                'specification_id': spec.id,
                'product_tmpl_id': pt.id,
                'parameter_id': mavi04.id,
                'evaluation_type': 'binary_selection',
                'sequence': seq,
                'active': True,
            })
            return True
        return False

    # PASO 3: Renombrar Rasgaduras (691) → Empaque
    if spec_ras_old in specs_activos:
        specs_activos[spec_ras_old].write({'specification_id': spec_ras_emp.id})
        stats['swap_ras'] += 1

    # PASO 3: Renombrar Deformidad (692) → Empaque
    if spec_def_old in specs_activos:
        specs_activos[spec_def_old].write({'specification_id': spec_def_emp.id})
        stats['swap_def'] += 1

    # PASO 4: Agregar Rasgaduras — Prueba si falta
    if add_spec(spec_ras_pru, 60):
        stats['add_ras_pru'] += 1

    # PASO 4: Agregar Deformidad — Prueba si falta
    if add_spec(spec_def_pru, 70):
        stats['add_def_pru'] += 1

print(f"\nRESUMEN:")
print(f"  Rasgaduras   → Empaque:        {stats['swap_ras']} productos")
print(f"  Deformidad   → Empaque:        {stats['swap_def']} productos")
print(f"  Rasgaduras — Prueba agregada:  {stats['add_ras_pru']} productos")
print(f"  Deformidad — Prueba agregada:  {stats['add_def_pru']} productos")
print(f"  Sin MAVI-04 (skip):            {stats['sin_mavi04']} productos")

env.cr.commit()
print("\n✓ Cambios guardados en staging.")
