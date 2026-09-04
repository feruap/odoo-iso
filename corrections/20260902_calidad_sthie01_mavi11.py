"""
STHIE01 Hielera chica — actualizar MAVI-11 y desactivar VAMA-023.

Cambios autorizados por Diana Flores, 2026-09-02:
  Ancho:  15.4 cm ± 0.5 cm  →  15-18 cm ± 0.5 cm
  Alto:   17.0 cm ± 0.5 cm  →  15-18 cm ± 0.5 cm
  Largo:  20.5 cm ± 0.5 cm  →  sin cambio
  Grosor:  2.5 cm ± 0.5 cm  →  2 cm ± 1 cm
  + Nueva spec en MAVI-11: Capacidad de cierre < 0.5 cm
  - Desactivar VAMA-023 (Capacidad de cierre)
"""
import json

SpecConf = env['amunet.quality.parameter.specification.config']
Rel      = env['amunet.quality.parameter.product.rel']
SpecBase = env['amunet.quality.check.parameter.specification']
Param    = env['amunet.quality.check.parameter']

# IDs activos actuales en STHIE01
ID_ANCHO  = 78014
ID_ALTO   = 78015
ID_LARGO  = 78016  # sin cambio
ID_GROSOR = 78017
ID_VAMA   = 78018  # Capacidad de cierre VAMA-023 → desactivar

# 1. Actualizar Ancho
s = SpecConf.browse(ID_ANCHO)
s.write({'acceptance_criteria': '15-18 cm ± 0.5 cm'})
print(f"[{ID_ANCHO}] Ancho → '{s.acceptance_criteria}'")

# 2. Actualizar Alto
s = SpecConf.browse(ID_ALTO)
s.write({'acceptance_criteria': '15-18 cm ± 0.5 cm'})
print(f"[{ID_ALTO}] Alto → '{s.acceptance_criteria}'")

# 3. Largo sin cambio
s = SpecConf.browse(ID_LARGO)
print(f"[{ID_LARGO}] Largo → sin cambio: '{s.acceptance_criteria}'")

# 4. Actualizar Grosor
s = SpecConf.browse(ID_GROSOR)
s.write({'acceptance_criteria': '2 cm ± 1 cm'})
print(f"[{ID_GROSOR}] Grosor → '{s.acceptance_criteria}'")

# 5. Desactivar VAMA-023
s = SpecConf.browse(ID_VAMA)
s.write({'active': False})
print(f"[{ID_VAMA}] VAMA-023 Capacidad de cierre → DESACTIVADO")

# 6. Agregar nueva spec de MAVI-11: Capacidad de cierre < 0.5 cm
param_mavi11 = Param.search([('code', '=', 'MAVI-11')], limit=1)
rel_mavi11 = Rel.search([
    ('product_tmpl_id', '=', 988),  # STHIE01
    ('parameter_id', '=', param_mavi11.id),
], limit=1)

# Buscar o crear spec base 'Capacidad de cierre' en MAVI-11
spec_base_cc = SpecBase.search([
    ('parameter_id', '=', param_mavi11.id),
    ('name', '=', 'Capacidad de cierre'),
], limit=1)
if not spec_base_cc:
    spec_base_cc = SpecBase.create({
        'parameter_id': param_mavi11.id,
        'name': 'Capacidad de cierre',
        'evaluation_type': 'numeric_range',
        'active': True,
    })
    print(f"Spec base MAVI-11/Capacidad de cierre creada id={spec_base_cc.id}")
else:
    print(f"Spec base MAVI-11/Capacidad de cierre id={spec_base_cc.id} ya existe")

# Ver si ya existe la spec config activa
ya_existe = SpecConf.with_context(active_test=False).search([
    ('product_parameter_rel_id', '=', rel_mavi11.id),
    ('specification_id', '=', spec_base_cc.id),
    ('active', '=', True),
], limit=1)
if not ya_existe:
    nueva = SpecConf.create({
        'product_parameter_rel_id': rel_mavi11.id,
        'specification_id': spec_base_cc.id,
        'active': True,
        'evaluation_type': 'numeric_range',
        'acceptance_criteria': '< 0.5 cm',
    })
    print(f"Nueva spec MAVI-11/Capacidad de cierre creada id={nueva.id} → '< 0.5 cm'")
else:
    ya_existe.write({'acceptance_criteria': '< 0.5 cm'})
    print(f"Spec MAVI-11/Capacidad de cierre ya existía [{ya_existe.id}] → '< 0.5 cm'")

env.cr.commit()
print("\n✓ STHIE01 Hielera chica actualizada correctamente.")
