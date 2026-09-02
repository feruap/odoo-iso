"""
Configuración de parámetros de calidad para Controles Negativos:
  - STCNL01: Control Negativo
  - STCON01:  Control negativo
  - SPCNL04:  Control Negativo VPH

Parámetros:
  1. MAVI-20 — Aspectos de reactivos liofilizados
       Widget: 4 binarios (Color, Forma, Textura, Humedad)
       Criterio positivo: blanco, compacto, sin textura pegajosa y sin humedad aparente.
  2. MAVI-07 — Visualización de líneas resultado base (NEGATIVO)
       Spec 1: Almacenamiento en refrigeración  → negativo, #5 CUMPLE; #1-4/#6/#7 NO CUMPLE
       Spec 2: Almacenamiento en temperatura ambiente → negativo, #5 CUMPLE; #1-4/#6/#7 NO CUMPLE

Idempotente — seguro de correr más de una vez.
Confirmado por Diana Flores, 2026-09-01.
"""

import json

CONTROLES = [
    ('STCNL01', 'Control Negativo',     'Control negativo'),
    ('STCON01', 'Control negativo',     'Control negativo'),
    ('SPCNL04', 'Control Negativo VPH', 'Control negativo'),
]

DESCRIPCION_MAP = {
    'STCNL01': 'Control negativo',
    'STCON01':  'Control negativo',
    'SPCNL04':  'Control negativo',
}

SPECS_ACTIVAS_MAVI20 = {'Aspectos del liofilizado'}
SPECS_ACTIVAS_MAVI07 = {'Almacenamiento en refrigeración', 'Almacenamiento en temperatura ambiente'}

MAPPING_MAVI20 = {
    "success_message": "Liofilizado blanco y compacto, sin textura pegajosa y sin humedad aparente.",
    "error_prefix": "Liofilizado mala apariencia",
    "positions": [
        {"index": 0, "type": "binary",
         "A": "Blanco", "B": "Amarillo",
         "label": "1. Color",
         "instruction": "Verificar el color del liofilizado."},
        {"index": 1, "type": "binary",
         "A": "Compacto", "B": "Deformado",
         "label": "2. Forma",
         "instruction": "Verificar la forma del liofilizado."},
        {"index": 2, "type": "binary",
         "A": "Sin textura pegajosa", "B": "Con textura pegajosa",
         "label": "3. Textura",
         "instruction": "Verificar la textura del liofilizado."},
        {"index": 3, "type": "binary",
         "A": "Sin humedad aparente", "B": "Con humedad aparente",
         "label": "4. Humedad",
         "instruction": "Verificar humedad aparente del liofilizado."},
    ]
}

MAPPING_MAVI07_NEGATIVO = {
    "fixed_sample_type": "negative",
    "positions": [{
        "index": 0,
        "type": "select",
        "label": "Patrón Observado (PRB-01)",
        "instruction": "Seleccione el patrón visualizado. Para control negativo CUMPLE solo el patrón #5.",
        "options": [
            {"label": "#1 (Línea T muy intensa)",        "value": "result_1"},
            {"label": "#2 (Línea T intensa)",            "value": "result_2"},
            {"label": "#3 (Línea T moderada)",           "value": "result_3"},
            {"label": "#4 (Línea T tenue)",              "value": "result_4"},
            {"label": "#5 (Sin línea T, solo línea C)", "value": "result_5"},
            {"label": "#6 (Inválida)",                   "value": "result_6"},
            {"label": "#7 (Inválida)",                   "value": "result_7"},
            {"label": "N/A (control no disponible)",     "value": "na"},
        ],
    }],
    "phrase_template": "Control negativo: Patrón {0}",
    "evaluation": {
        "rules": [
            {"sample_type": "negative", "result": "result_1", "verdict": "fail",
             "message": "Control Negativo: Patrón #1 (línea T muy intensa) - NO CUMPLE"},
            {"sample_type": "negative", "result": "result_2", "verdict": "fail",
             "message": "Control Negativo: Patrón #2 (línea T intensa) - NO CUMPLE"},
            {"sample_type": "negative", "result": "result_3", "verdict": "fail",
             "message": "Control Negativo: Patrón #3 (línea T moderada) - NO CUMPLE"},
            {"sample_type": "negative", "result": "result_4", "verdict": "fail",
             "message": "Control Negativo: Patrón #4 (línea T tenue) - NO CUMPLE"},
            {"sample_type": "negative", "result": "result_5", "verdict": "pass",
             "message": "Control Negativo: Patrón #5 (solo línea C) - CUMPLE"},
            {"sample_type": "negative", "result": "result_6", "verdict": "fail",
             "message": "Control Negativo: Patrón #6 (inválida) - NO CUMPLE"},
            {"sample_type": "negative", "result": "result_7", "verdict": "fail",
             "message": "Control Negativo: Patrón #7 (inválida) - NO CUMPLE"},
            {"sample_type": "negative", "result": "na", "verdict": "not_applicable",
             "message": "Control Negativo: Control no disponible - N/A"},
        ]
    }
}

# ── Contexto (permite crear relaciones sin bloqueo de gobernanza) ─────────────
env = env(context=dict(env.context, amunet_alta_autorizada=True))

# ── Modelos ───────────────────────────────────────────────────────────────────
Param    = env['amunet.quality.check.parameter']
SpecBase = env['amunet.quality.check.parameter.specification']
Rel      = env['amunet.quality.parameter.product.rel']
SpecConf = env['amunet.quality.parameter.specification.config']
ProdTmpl = env['product.template']
ProdCat  = env['product.category']
QCheck   = env['amunet.quality.check']

# ── Parámetros ───────────────────────────────────────────────────────────────
param_mavi20 = Param.search([('code', '=', 'MAVI-20')], limit=1)
if not param_mavi20:
    param_mavi20 = Param.create({
        'code': 'MAVI-20',
        'name': 'Aspectos de reactivos liofilizados',
    })
    print(f"Parámetro MAVI-20 creado id={param_mavi20.id}")
else:
    print(f"Parámetro MAVI-20 id={param_mavi20.id} — {param_mavi20.name}")

param_mavi07 = Param.search([('code', '=', 'MAVI-07')], limit=1)
if not param_mavi07:
    raise ValueError("No se encontró parámetro MAVI-07")
print(f"Parámetro MAVI-07 id={param_mavi07.id}")

# ── Especificaciones base ─────────────────────────────────────────────────────
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
    print(f"  Spec base MAVI-20/Aspectos del liofilizado creada id={spec_base_mavi20.id}")
else:
    print(f"  Spec base MAVI-20/Aspectos del liofilizado id={spec_base_mavi20.id}")

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
        print(f"  Spec base MAVI-07/{spec_nombre} creada")

mapping_mavi20_json = json.dumps(MAPPING_MAVI20,         ensure_ascii=False)
mapping_mavi07_json = json.dumps(MAPPING_MAVI07_NEGATIVO, ensure_ascii=False)

CRIT_MAVI20 = 'Liofilizado blanco y compacto, sin textura pegajosa y sin humedad aparente.'
CRIT_MAVI07 = 'Patrón #5 (solo línea C)'

cat_control = ProdCat.search([('name', '=', 'Control')], limit=1)
if not cat_control:
    cat_control = ProdCat.create({'name': 'Control'})

creadas = desactivadas = actualizadas = 0

for codigo, nombre, _desc in CONTROLES:
    tmpl = ProdTmpl.search([('default_code', '=', codigo)], limit=1)
    if not tmpl:
        tmpl = ProdTmpl.create({
            'name': nombre, 'default_code': codigo,
            'type': 'consu', 'categ_id': cat_control.id,
        })
        print(f"  Producto creado: {codigo}")

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
            creadas += 1

        todas = SpecConf.with_context(active_test=False).search([
            ('product_parameter_rel_id', '=', rel.id),
        ])
        nombres_activos_encontrados = set()
        for sc in todas:
            if sc.specification_name in specs_activas:
                sc.write({
                    'active':              True,
                    'evaluation_type':     'vama_multi_check',
                    'acceptance_criteria': criterio,
                    'text_phrase_mapping': mapping_json,
                })
                nombres_activos_encontrados.add(sc.specification_name)
                actualizadas += 1
            else:
                if sc.active:
                    sc.write({'active': False})
                    desactivadas += 1

        # Crear specs faltantes
        for spec_nombre in specs_activas:
            if spec_nombre not in nombres_activos_encontrados:
                spec_b = SpecBase.search([
                    ('parameter_id', '=', param.id),
                    ('name', '=', spec_nombre),
                ], limit=1)
                if spec_b:
                    SpecConf.create({
                        'product_parameter_rel_id': rel.id,
                        'specification_id':         spec_b.id,
                        'active':                   True,
                        'evaluation_type':          'vama_multi_check',
                        'acceptance_criteria':      criterio,
                        'text_phrase_mapping':      mapping_json,
                    })
                    creadas += 1
                    print(f"    Spec config creada: {codigo}/{spec_nombre}")

print(f"\nRelaciones/configs creadas: {creadas}")
print(f"Specs actualizadas:          {actualizadas}")
print(f"Specs desactivadas:          {desactivadas}")

# ── Descripción en productos ──────────────────────────────────────────────────
print("\n── Configurando descripción en productos de control negativo ──")
Product = env['product.product']
for codigo, _nombre, desc in CONTROLES:
    prod = Product.search([('default_code', '=', codigo)], limit=1)
    if prod:
        desc_json = json.dumps({'en_US': desc}, ensure_ascii=False)
        env.cr.execute(
            "UPDATE product_template SET description = %s WHERE id = %s",
            (desc_json, prod.product_tmpl_id.id)
        )
        print(f"  {codigo}: {desc}")

# ── ANEXO CONTROL NEGATIVO en análisis abiertos ───────────────────────────────
print("\n── Configurando ANEXO CONTROL NEGATIVO en análisis abiertos ──")
codigos_neg = [c[0] for c in CONTROLES]
checks_neg = QCheck.search([
    ('product_id.default_code', 'in', codigos_neg),
    ('state', 'not in', ('done', 'cancel')),
])
anexo_config = {
    'tiene_anexos':      True,
    'anexo_titulo':      'ANEXO CONTROL NEGATIVO',
    'anexo_col1_header': 'Apariencia',
    'anexo_col2_header': 'Liberación',
    'anexo_col3_header': 'Migración',
    'anexo_col4_header': 'Observación',
    'anexo_col5_header': '',
    'anexo_col6_header': '',
    'anexo_col7_header': '',
    'anexo_col8_header': '',
}
checks_neg.write(anexo_config)
print(f"  Análisis actualizados con anexo: {len(checks_neg)}")

actualizados_desc = 0
for check in checks_neg:
    codigo = check.product_id.default_code or ''
    desc = DESCRIPCION_MAP.get(codigo, '')
    if desc:
        check.write({'product_description': desc})
        actualizados_desc += 1
print(f"  Análisis actualizados con descripción: {actualizados_desc}")

# ── Actualizar detail lines de análisis abiertos ─────────────────────────────
print("\n── Actualizando parámetros en líneas de análisis abiertos ──")
Detail = env['amunet.quality.test.line.detail']
for check in checks_neg:
    for line in check.test_line_ids:
        # CORREGIDO 2026-09-01 (PM, autorizado por Mery): el campo se llama
        # detail_line_ids, no detail_ids. Con el nombre viejo el script
        # reventaba en cuanto tocaba un analisis que SI tenia lineas.
        for detail in line.detail_line_ids:
            if detail.evaluation_type == 'vama_multi_check':
                mapping_json = None
                # Detectar si es MAVI-20 (por el nombre del parámetro)
                param_name = detail.parameter_id.code if detail.parameter_id else ''
                if param_name == 'MAVI-20':
                    mapping_json = mapping_mavi20_json
                elif param_name == 'MAVI-07':
                    mapping_json = mapping_mavi07_json
                if mapping_json:
                    detail.write({'text_phrase_mapping': mapping_json})
                    print(f"    Análisis {check.name}: detalle {detail.id} ({param_name}) actualizado")

# ── Códigos de reporte, certificado y referencias ────────────────────────────
print("\n── Configurando códigos de reporte y referencias ──")
REFS_NEGATIVO = '- ESPST-039\n- Técnica de análisis TAST-039'

for codigo in ['STCON01', 'STCNL01', 'SPCNL04']:
    env.cr.execute("""
        UPDATE product_template SET
            report_document_code       = 'RAST-039',
            report_version             = 4,
            report_effective_date      = '2025-08-01',
            certificate_document_code  = 'CERST-039',
            certificate_version        = 4,
            certificate_effective_date = '2025-08-01',
            report_references          = %s
        WHERE default_code = %s
    """, (REFS_NEGATIVO, codigo))
    print(f"  {codigo}: RAST-039 / CERST-039 rev04 Ago.2025")

env.cr.commit()
print("\n✓ Script completado — STCNL01, STCON01, SPCNL04 configurados con MAVI-20 (4 binarios) + MAVI-07 negativo + ANEXO + códigos de reporte.")
