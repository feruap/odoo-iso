"""
Actualiza STHIS01 (Hisopo Nasofaríngeo):
  1. Renombra sección MAVI-04 "Estructura del hisopo" → "Apariencia del hisopo"
  2. Cambia tolerancia de ±2 mm (y ±1 mm) a ±5 mm en todas las medidas MAVI-11

Medidas actualizadas y sus nuevos rangos:
  Longitud del mango            127 ± 5 → 122–132
  Longitud de la mota            21 ± 5 →  16–26
  Punto de quiebre               80 ± 5 →  75–85
  Longitud del hisopo completo  148 ± 5 → 143–153
  Longitud total del cepillo    200 ± 5 → 195–205
  Longitud del mango del cepillo 161 ± 5 → 156–166
  Longitud de la cabeza cepillo  39 ± 5 →  34–44
  Hisopo retraído completo      130 ± 5 → 125–135
  Hisopo extendido completo     160 ± 5 → 155–165
  Ancho                         200 ± 5 → 195–205
  Largo                         300 ± 5 → 295–305
  (Grosor 0.68 ± 0.08 mm — sin cambio, tolerancia diferente)

Autorizado por: Diana Flores (s.controldecalidad@amunet.com.mx)
Fecha: 2026-08-21
"""

tmpl = env['product.template'].with_context(active_test=False).search(
    [('default_code', '=', 'STHIS01')], limit=1)
if not tmpl:
    print("ERROR: STHIS01 no encontrado")
    raise SystemExit(1)

tmpl_id = tmpl.id
ParamRel = env['amunet.quality.parameter.product.rel']
SpecCfg  = env['amunet.quality.parameter.specification.config']

# 1. Renombrar sección "Estructura del hisopo" → "Apariencia del hisopo"
rel_estructura = ParamRel.search([
    ('product_tmpl_id', '=', tmpl_id),
    ('parameter_name', 'ilike', 'Estructura'),
], limit=1)
if rel_estructura:
    rel_estructura.sudo().write({'parameter_name': 'Apariencia del hisopo'})
    print(f"  Renombrado rel {rel_estructura.id}: Estructura del hisopo → Apariencia del hisopo")
else:
    print("  AVISO: rel 'Estructura del hisopo' no encontrado (¿ya renombrado?)")

# 2. Actualizar medidas MAVI-11 con ±5 mm
medidas = [
    ('Longitud del mango',             '127 mm ± 5 mm', 122, 132),
    ('Longitud de la mota',            '21 mm ± 5 mm',   16,  26),
    ('Punto de quiebre',               '80 mm ± 5 mm',   75,  85),
    ('Longitud del hisopo completo',   '148 mm ± 5 mm', 143, 153),
    ('Longitud total del cepillo',     '200 mm ± 5 mm', 195, 205),
    ('Longitud del mango del cepillo', '161 mm ± 5 mm', 156, 166),
    ('Longitud de la cabeza del cepillo', '39 mm ± 5 mm', 34, 44),
    ('Longitud del hisopo retraído completo',  '130 mm ± 5 mm', 125, 135),
    ('Longitud del hisopo extendido completo', '160 mm ± 5 mm', 155, 165),
    ('Ancho',  '200 mm ± 5 mm', 195, 205),
    ('Largo',  '300 mm ± 5 mm', 295, 305),
]

rel_mavi11 = ParamRel.search([
    ('product_tmpl_id', '=', tmpl_id),
    ('parameter_code', '=', 'MAVI-11'),
], limit=1)
if not rel_mavi11:
    print("ERROR: MAVI-11 rel no encontrado para STHIS01")
    raise SystemExit(1)

for spec_name, criteria, vmin, vmax in medidas:
    cfg = SpecCfg.search([
        ('product_parameter_rel_id', '=', rel_mavi11.id),
        ('specification_name', '=', spec_name),
    ], limit=1)
    if cfg:
        cfg.sudo().write({
            'acceptance_criteria': criteria,
            'min_value': vmin,
            'max_value': vmax,
        })
        print(f"  ✅ {spec_name}: {criteria} ({vmin}–{vmax})")
    else:
        print(f"  ⚠️  No encontrado: {spec_name}")

env.cr.commit()
print("\n✅ STHIS01 — medidas actualizadas a ±5 mm y sección renombrada.")
