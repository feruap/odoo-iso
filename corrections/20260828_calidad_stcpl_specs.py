"""
Configuración de parámetros de calidad para Controles Positivos STCPL01-16.

Parámetros por producto:
  1. MAVI-20 — Aspectos de reactivos liofilizados
       Criterio: Blanco, compacto, sin textura pegajosa y sin humedad aparente
       Widget: 4 binarios (Color, Forma, Textura, Humedad)
  2. MAVI-07 — Visualización de líneas resultado base
       Spec 1: Almacenamiento en refrigeración  → positivo, #1-4 cumple, #5 no cumple
       Spec 2: Almacenamiento en temperatura ambiente → positivo, #1-4 cumple, #5 no cumple

MAVI-20 reemplaza a VAMA-078. Si MAVI-20 no existe en la BD, se crea.
Las relaciones STCPL-VAMA-078 creadas anteriormente se eliminan.
Todas las demás specs generadas automáticamente se desactivan.

Idempotente — seguro de correr más de una vez.
Confirmado por Diana Flores, 2026-08-28.
"""

import json

CONTROLES = [
    ('STCPL01', 'Control Positivo SARS-CoV-2'),
    ('STCPL02', 'Control Positivo Influenza A+B'),
    ('STCPL03', 'Control Positivo Tuberculosis'),
    ('STCPL04', 'Control Positivo VPH NET'),
    ('STCPL05', 'Control Positivo K-RAS'),
    ('STCPL06', 'Control Positivo P/anticuerpos VIH tipo 1'),
    ('STCPL07', 'Control Positivo P/anticuerpos VIH tipo 2'),
    ('STCPL08', 'Control Positivo Tuberculosis TB'),
    ('STCPL09', 'Control Positivo Tuberculosis RIF/INH'),
    ('STCPL10', 'Control Positivo Isolister-ADN'),
    ('STCPL11', 'Control Positivo AUREUS-ADN'),
    ('STCPL12', 'Control Positivo CAMPY-ADN'),
    ('STCPL13', 'Control Positivo ENTERONET-ADN'),
    ('STCPL14', 'Control Positivo SALMONET-ADN'),
    ('STCPL15', 'Control Positivo EcoHem-ADN'),
    ('STCPL16', 'Control Positivo VIHLAMP-ADN'),
]

SPECS_ACTIVAS_MAVI20 = {'Aspectos del liofilizado'}
SPECS_ACTIVAS_MAVI07 = {'Almacenamiento en refrigeración', 'Almacenamiento en temperatura ambiente'}

MAPPING_MAVI20 = {
    "positions": [
        {"index": 0, "type": "binary",
         "A": "Blanco, compacto y sin humedad aparente",
         "B": "No cumple",
         "label": "Apariencia",
         "instruction": "Verificar que el liofilizado sea blanco, compacto y sin humedad aparente."},
    ]
}

MAPPING_MAVI07_POSITIVO = {
    "fixed_sample_type": "positive",
    "positions": [{
        "index": 0,
        "type": "select",
        "label": "Patrón Observado (PRB-01)",
        "instruction": "Seleccione el patrón visualizado.",
        "options": [
            {"label": "#1 (Línea T muy intensa)", "value": "result_1"},
            {"label": "#2 (Línea T intensa)",     "value": "result_2"},
            {"label": "#3 (Línea T moderada)",    "value": "result_3"},
            {"label": "#4 (Línea T tenue)",       "value": "result_4"},
            {"label": "#5 (Sin línea T, solo línea C)", "value": "result_5"},
            {"label": "N/A (control no disponible)",    "value": "na"},
        ],
    }],
    "phrase_template": "Control positivo: Patrón {0}",
    "evaluation": {
        "rules": [
            {"sample_type": "positive", "result": "result_1", "verdict": "pass",
             "message": "Control Positivo: Patrón #1 (línea T muy intensa) - CUMPLE"},
            {"sample_type": "positive", "result": "result_2", "verdict": "pass",
             "message": "Control Positivo: Patrón #2 (línea T intensa) - CUMPLE"},
            {"sample_type": "positive", "result": "result_3", "verdict": "pass",
             "message": "Control Positivo: Patrón #3 (línea T moderada) - CUMPLE"},
            {"sample_type": "positive", "result": "result_4", "verdict": "pass",
             "message": "Control Positivo: Patrón #4 (línea T tenue) - CUMPLE"},
            {"sample_type": "positive", "result": "result_5", "verdict": "fail",
             "message": "Control Positivo: Patrón #5 (sin línea T) - NO CUMPLE"},
            {"sample_type": "positive", "result": "na",       "verdict": "not_applicable",
             "message": "Control Positivo: Control no disponible - N/A"},
        ]
    }
}

# ── Modelos ───────────────────────────────────────────────────────────────────
Param    = env['amunet.quality.check.parameter']
SpecBase = env['amunet.quality.check.parameter.specification']
Rel      = env['amunet.quality.parameter.product.rel']
SpecConf = env['amunet.quality.parameter.specification.config']
ProdTmpl = env['product.template']
ProdCat  = env['product.category']

# ── MAVI-20: crear si no existe ───────────────────────────────────────────────
param_mavi20 = Param.search([('code', '=', 'MAVI-20')], limit=1)
if not param_mavi20:
    param_mavi20 = Param.create({
        'code': 'MAVI-20',
        'name': 'Aspectos de reactivos liofilizados',
    })
    print(f"Parámetro MAVI-20 creado id={param_mavi20.id}")
else:
    print(f"Parámetro MAVI-20 id={param_mavi20.id} — {param_mavi20.name}")

# ── Especificación base "Aspectos del liofilizado" para MAVI-20 ───────────────
spec_base_mavi20 = SpecBase.search([
    ('parameter_id', '=', param_mavi20.id),
    ('name', '=', 'Aspectos del liofilizado'),
], limit=1)
if not spec_base_mavi20:
    spec_base_mavi20 = SpecBase.create({
        'parameter_id':    param_mavi20.id,
        'name':            'Aspectos del liofilizado',
        'evaluation_type': 'vama_multi_check',
        'active':          True,
    })
    print(f"  Spec base MAVI-20 / Aspectos del liofilizado creada id={spec_base_mavi20.id}")
else:
    print(f"  Spec base MAVI-20 / Aspectos del liofilizado id={spec_base_mavi20.id}")

# ── MAVI-07 ───────────────────────────────────────────────────────────────────
param_mavi07 = Param.search([('code', '=', 'MAVI-07')], limit=1)
if not param_mavi07:
    raise ValueError("No se encontró parámetro MAVI-07")
print(f"Parámetro MAVI-07 id={param_mavi07.id}")

for spec_nombre in ['Almacenamiento en refrigeración', 'Almacenamiento en temperatura ambiente']:
    spec = SpecBase.search([
        ('parameter_id', '=', param_mavi07.id),
        ('name', '=', spec_nombre),
    ], limit=1)
    if not spec:
        SpecBase.create({
            'parameter_id':    param_mavi07.id,
            'name':            spec_nombre,
            'evaluation_type': 'vama_multi_check',
            'active':          True,
        })
        print(f"  Spec base MAVI-07 / {spec_nombre} creada")

# ── VAMA-078: obtener para limpiar relaciones previas ────────────────────────
param_vama078 = Param.search([
    ('code', '=', 'VAMA-078'), ('name', '=', 'Aspectos del liofilizado')
], limit=1)

cat_control = ProdCat.search([('name', '=', 'Control')], limit=1)
if not cat_control:
    cat_control = ProdCat.create({'name': 'Control'})

mapping_mavi20_json = json.dumps(MAPPING_MAVI20,          ensure_ascii=False)
mapping_mavi07_json = json.dumps(MAPPING_MAVI07_POSITIVO,  ensure_ascii=False)

CRIT_MAVI20 = 'Liofilizado blanco y compacto, sin textura pegajosa y sin humedad aparente.'
CRIT_MAVI07 = '#1, #2, #3 y #4'

eliminadas  = 0
desactivadas = 0
actualizadas  = 0

for codigo, nombre in CONTROLES:
    tmpl = ProdTmpl.search([('default_code', '=', codigo)], limit=1)
    if not tmpl:
        tmpl = ProdTmpl.create({
            'name': nombre, 'default_code': codigo,
            'type': 'consu', 'categ_id': cat_control.id,
        })
        print(f"  Producto creado: {codigo}")

    # Desactivar todas las specs de VAMA-078 (reemplazado por MAVI-20)
    if param_vama078:
        rel_vama = Rel.search([
            ('product_tmpl_id', '=', tmpl.id),
            ('parameter_id',    '=', param_vama078.id),
        ], limit=1)
        if rel_vama:
            sc_vama = SpecConf.with_context(active_test=False).search([
                ('product_parameter_rel_id', '=', rel_vama.id),
                ('active', '=', True),
            ])
            if sc_vama:
                sc_vama.write({'active': False})
                eliminadas += len(sc_vama)

    # Procesar MAVI-20 y MAVI-07
    for param, specs_activas, mapping_json, criterio in [
        (param_mavi20, SPECS_ACTIVAS_MAVI20, mapping_mavi20_json, CRIT_MAVI20),
        (param_mavi07, SPECS_ACTIVAS_MAVI07, mapping_mavi07_json, CRIT_MAVI07),
    ]:
        rel = Rel.search([
            ('product_tmpl_id', '=', tmpl.id),
            ('parameter_id',    '=', param.id),
        ], limit=1)
        if not rel:
            rel = Rel.create({
                'product_tmpl_id': tmpl.id,
                'parameter_id':    param.id,
            })

        todas = SpecConf.with_context(active_test=False).search([
            ('product_parameter_rel_id', '=', rel.id),
        ])
        for sc in todas:
            if sc.specification_name in specs_activas:
                sc.write({
                    'active':              True,
                    'evaluation_type':     'vama_multi_check',
                    'acceptance_criteria': criterio,
                    'text_phrase_mapping': mapping_json,
                })
                actualizadas += 1
            else:
                if sc.active:
                    sc.write({'active': False})
                    desactivadas += 1

print(f"\nSpecs VAMA-078 desactivadas:    {eliminadas}")
print(f"Specs actualizadas (activas):   {actualizadas}")
print(f"Specs desactivadas:             {desactivadas}")
env.cr.commit()
print("\n✓ Script completado — STCPL01-16 configurados con MAVI-20 + MAVI-07.")
