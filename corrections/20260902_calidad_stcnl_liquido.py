"""
Corrección: controles negativos son líquidos, no liofilizados.

STCNL01, STCON01, SPCNL04 → quitar MAVI-20, agregar MGA-0981 + MAVI-13.
Criterios:
  - MGA-0981 Variación de volumen: 60 µL ± 10 µL (min=50, max=70)
  - MAVI-13 Bloqueo de la luz por partículas: Sin partículas suspendidas

Análisis 785 (STCNL01, in_progress):
  - Línea 2633 (MAVI-20): marcar como N/A
  - Agregar líneas nuevas para MGA-0981 y MAVI-13

Confirmado por Diana Flores, 2026-09-02.
Idempotente — seguro de correr más de una vez.
"""

import json

env = env(context=dict(env.context, amunet_alta_autorizada=True))

Param    = env['amunet.quality.check.parameter']
SpecBase = env['amunet.quality.check.parameter.specification']
Rel      = env['amunet.quality.parameter.product.rel']
SpecConf = env['amunet.quality.parameter.specification.config']
ProdTmpl = env['product.template']
QCheck   = env['amunet.quality.check']
QLine    = env['amunet.quality.test.line']
QDetail  = env['amunet.quality.test.line.detail']

CONTROLES = ['STCNL01', 'STCON01', 'SPCNL04']

# ── Parámetros ─────────────────────────────────────────────────────────────────
param_mavi20 = Param.search([('code', '=', 'MAVI-20')], limit=1)
param_mavi13 = Param.browse(71)   # "Bloqueo de la luz por partículas"
param_mga    = Param.browse(80)   # "Variación de volumen" MGA-0981

print(f"MAVI-20 id={param_mavi20.id} | MAVI-13 id={param_mavi13.id} name={param_mavi13.name}"
      f" | MGA-0981 id={param_mga.id} name={param_mga.name}")

# ── Spec base MGA-0981 numeric_range para controles ────────────────────────────
spec_mga = SpecBase.search([
    ('parameter_id', '=', param_mga.id),
    ('name', '=', 'Variación de volumen'),
    ('evaluation_type', '=', 'numeric_range'),
], limit=1)
if not spec_mga:
    # Usar la id=144 que ya existe
    spec_mga = SpecBase.browse(144)
print(f"Spec MGA base: id={spec_mga.id} name={spec_mga.name} eval={spec_mga.evaluation_type}")

# ── Spec base MAVI-13 binary_selection para controles ──────────────────────────
spec_mavi13 = SpecBase.browse(74)  # "Partículas en solución" binary_selection
print(f"Spec MAVI-13 base: id={spec_mavi13.id} name={spec_mavi13.name} eval={spec_mavi13.evaluation_type}")

# ── Para cada producto: desactivar MAVI-20, activar MGA-0981 + MAVI-13 ─────────
for codigo in CONTROLES:
    tmpl = ProdTmpl.search([('default_code', '=', codigo)], limit=1)
    if not tmpl:
        print(f"  {codigo}: producto NO encontrado — saltar")
        continue
    print(f"\n── {codigo} (tmpl id={tmpl.id}) ──")

    # 1. Desactivar relación MAVI-20
    if param_mavi20:
        rel_mavi20 = Rel.with_context(active_test=False).search([
            ('product_tmpl_id', '=', tmpl.id),
            ('parameter_id', '=', param_mavi20.id),
        ], limit=1)
        if rel_mavi20:
            confs = SpecConf.with_context(active_test=False).search([
                ('product_parameter_rel_id', '=', rel_mavi20.id),
            ])
            confs.write({'active': False})
            print(f"  MAVI-20: {len(confs)} spec(s) desactivadas")
        else:
            print(f"  MAVI-20: sin relación — ok")

    # 2. Crear/actualizar relación MGA-0981
    rel_mga = Rel.with_context(active_test=False).search([
        ('product_tmpl_id', '=', tmpl.id),
        ('parameter_id', '=', param_mga.id),
    ], limit=1)
    if not rel_mga:
        rel_mga = Rel.create({
            'product_tmpl_id': tmpl.id,
            'parameter_id': param_mga.id,
        })
        print(f"  MGA-0981 rel creada id={rel_mga.id}")
    else:
        print(f"  MGA-0981 rel existe id={rel_mga.id}")

    # Buscar o crear spec config MGA-0981
    sc_mga = SpecConf.with_context(active_test=False).search([
        ('product_parameter_rel_id', '=', rel_mga.id),
    ], limit=1)
    mga_vals = {
        'active': True,
        'evaluation_type': 'numeric_range',
        'acceptance_criteria': '60 µL ± 10 µL',
        'min_value': 50.0,
        'max_value': 70.0,
    }
    if sc_mga:
        sc_mga.write(mga_vals)
        print(f"  MGA-0981 spec config actualizada id={sc_mga.id}")
    else:
        mga_vals.update({
            'product_parameter_rel_id': rel_mga.id,
            'specification_id': spec_mga.id,
        })
        sc_mga = SpecConf.create(mga_vals)
        print(f"  MGA-0981 spec config creada id={sc_mga.id}")

    # 3. Crear/actualizar relación MAVI-13
    rel_mavi13 = Rel.with_context(active_test=False).search([
        ('product_tmpl_id', '=', tmpl.id),
        ('parameter_id', '=', param_mavi13.id),
    ], limit=1)
    if not rel_mavi13:
        rel_mavi13 = Rel.create({
            'product_tmpl_id': tmpl.id,
            'parameter_id': param_mavi13.id,
        })
        print(f"  MAVI-13 rel creada id={rel_mavi13.id}")
    else:
        print(f"  MAVI-13 rel existe id={rel_mavi13.id}")

    sc_mavi13 = SpecConf.with_context(active_test=False).search([
        ('product_parameter_rel_id', '=', rel_mavi13.id),
    ], limit=1)
    mavi13_vals = {
        'active': True,
        'evaluation_type': 'binary_selection',
        'acceptance_criteria': 'Sin partículas suspendidas',
    }
    if sc_mavi13:
        sc_mavi13.write(mavi13_vals)
        print(f"  MAVI-13 spec config actualizada id={sc_mavi13.id}")
    else:
        mavi13_vals.update({
            'product_parameter_rel_id': rel_mavi13.id,
            'specification_id': spec_mavi13.id,
        })
        sc_mavi13 = SpecConf.create(mavi13_vals)
        print(f"  MAVI-13 spec config creada id={sc_mavi13.id}")

# ── Análisis 785: marcar MAVI-20 como N/A + agregar líneas MGA-0981 y MAVI-13 ──
print("\n── Actualizar análisis 785 ──")
check = QCheck.sudo().browse(785)
print(f"  estado={check.state} producto={check.product_id.default_code}")

# Marcar línea 2633 (MAVI-20) y su detail como N/A vía SQL (campo computado almacenado)
env.cr.execute("""
    UPDATE amunet_quality_test_line_detail
    SET verdict = 'not_applicable'
    WHERE id = 7579
""")
rows_det = env.cr.rowcount
env.cr.execute("""
    UPDATE amunet_quality_test_line
    SET verdict = 'not_applicable'
    WHERE id = 2633
""")
rows_line = env.cr.rowcount
if rows_line > 0:
    print(f"  Línea 2633 (MAVI-20) marcada N/A vía SQL ({rows_det} detail, {rows_line} line)")
else:
    print(f"  Línea 2633 no encontrada en producción — ok")

# Intentar agregar líneas nuevas al análisis 785 (in_progress)
# Buscar rel y spec config para el producto STCNL01
tmpl_cnl = ProdTmpl.search([('default_code', '=', 'STCNL01')], limit=1)
prod_cnl  = tmpl_cnl.product_variant_ids[:1] if tmpl_cnl else None

if prod_cnl:
    rel_mga_cnl = Rel.search([
        ('product_tmpl_id', '=', tmpl_cnl.id),
        ('parameter_id', '=', param_mga.id),
    ], limit=1)
    rel_mavi13_cnl = Rel.search([
        ('product_tmpl_id', '=', tmpl_cnl.id),
        ('parameter_id', '=', param_mavi13.id),
    ], limit=1)
    sc_mga_cnl   = SpecConf.search([('product_parameter_rel_id', '=', rel_mga_cnl.id)], limit=1) if rel_mga_cnl else None
    sc_m13_cnl   = SpecConf.search([('product_parameter_rel_id', '=', rel_mavi13_cnl.id)], limit=1) if rel_mavi13_cnl else None

    # ── MGA-0981 ──
    ya_tiene_mga = QLine.sudo().search([
        ('check_id', '=', 785),
        ('parameter_rel_id', '=', rel_mga_cnl.id if rel_mga_cnl else 0),
    ], limit=1)
    if ya_tiene_mga:
        print(f"  Línea MGA-0981 ya existe en análisis 785 (id={ya_tiene_mga.id})")
    elif rel_mga_cnl and sc_mga_cnl:
        try:
            new_line_mga = QLine.sudo().create({
                'check_id': 785,
                'parameter_rel_id': rel_mga_cnl.id,
                'name': 'Variación de volumen',
            })
            QDetail.sudo().create({
                'test_line_id': new_line_mga.id,
                'name': 'Variación de volumen',
                'specification_config_id': sc_mga_cnl.id,
                'specification_id': spec_mga.id,
                'evaluation_type': 'numeric_range',
                'acceptance_criteria': '60 µL ± 10 µL',
                'min_value': 50.0,
                'max_value': 70.0,
            })
            print(f"  Línea MGA-0981 creada id={new_line_mga.id}")
        except Exception as e:
            print(f"  No se pudo agregar MGA-0981: {e}")
    else:
        print(f"  Sin rel/spec para MGA-0981 — no se puede agregar línea")

    # ── MAVI-13 ──
    ya_tiene_m13 = QLine.sudo().search([
        ('check_id', '=', 785),
        ('parameter_rel_id', '=', rel_mavi13_cnl.id if rel_mavi13_cnl else 0),
    ], limit=1)
    if ya_tiene_m13:
        print(f"  Línea MAVI-13 ya existe en análisis 785 (id={ya_tiene_m13.id})")
    elif rel_mavi13_cnl and sc_m13_cnl:
        try:
            new_line_m13 = QLine.sudo().create({
                'check_id': 785,
                'parameter_rel_id': rel_mavi13_cnl.id,
                'name': 'Bloqueo de la luz por partículas',
            })
            QDetail.sudo().create({
                'test_line_id': new_line_m13.id,
                'name': 'Partículas en solución',
                'specification_config_id': sc_m13_cnl.id,
                'specification_id': spec_mavi13.id,
                'evaluation_type': 'binary_selection',
                'acceptance_criteria': 'Sin partículas suspendidas',
            })
            print(f"  Línea MAVI-13 creada id={new_line_m13.id}")
        except Exception as e:
            print(f"  No se pudo agregar MAVI-13: {e}")
    else:
        print(f"  Sin rel/spec para MAVI-13 — no se puede agregar línea")

env.cr.commit()
print("\n✓ Script completado — controles negativos corregidos a líquido.")
