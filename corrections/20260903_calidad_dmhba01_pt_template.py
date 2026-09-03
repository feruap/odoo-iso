"""
Restaura la configuración del template PT Cualitativas para DMHBA01 (Hemoglobina Cualitativa).
Parámetros: MAVI-04 (Empaque+Prueba), MAVI-07 (neg/pos), MAVI-09 (lib/migración),
            MGA-0486 (Hermeticidad), INC-002 (Contenido).
Análisis de referencia: 865 (QC/2026/00121) y 870 (QC/2026/00130).
Columnas del Anexo Cartucho: Apariencia Empaque / Prueba / Hermeticidad /
                             Contenido / T.Lib / T.Mig / Desempeño.
"""
import json

# ── IDs fijos ──────────────────────────────────────────────────────────────
TMPL_ID  = 1315   # product.template DMHBA01
REL_MAVI04  = 3708
REL_MAVI07  = 3709
REL_MAVI09  = 3710

# ── MAVI-04 SpecConf activos ────────────────────────────────────────────────
# sc 84223 Sin polvo       84224 Sin manchas  84225 Sin rasgaduras
# sc 84226 Sin deformidad  84227 Letra adecuada
# sc 89409 Sin rasgaduras — Prueba   89410 Sin deformidad — Prueba
MAVI04_SCS = {
    84223: ('Sin polvo',                    'Sin/Con', 'Sin polvo',           'Con polvo',           'with_prefix', 10),
    84224: ('Sin manchas y/o suciedad',     'Sin/Con', 'Sin manchas',         'Con manchas',         'with_prefix', 20),
    84225: ('Sin rasgaduras',               'Sin/Con', 'Sin rasgaduras',      'Con rasgaduras',      'with_prefix', 30),
    84227: ('Letra adecuada',               'Letra adecuada/Letra inadecuada',
                                             'Letra adecuada', 'Letra inadecuada', 'with_prefix', 40),
    84226: ('Sin deformidad o deterioro',   'Sin/Con', 'Sin deformidad',      'Con deformidad',      'with_prefix', 50),
    89409: ('Sin rasgaduras — Prueba',      'Sin/Con', 'Sin rasgaduras',      'Con rasgaduras',      'with_prefix', 60),
    89410: ('Sin deformidad o deterioro — Prueba',
                                             'Sin/Con', 'Sin deformidad',     'Con deformidad',      'with_prefix', 70),
}

# ── MAVI-07 vama_multi_check mapping ───────────────────────────────────────
_OPTS = [
    {"label": "#1 (Línea T muy intensa)",            "value": "result_1"},
    {"label": "#2 (Línea T intensa)",                "value": "result_2"},
    {"label": "#3 (Línea T moderada)",               "value": "result_3"},
    {"label": "#4 (Línea T tenue)",                  "value": "result_4"},
    {"label": "#5 (Sin línea T, solo línea C)",      "value": "result_5"},
    {"label": "#6 (Sin línea C, con línea T)",       "value": "result_6"},
    {"label": "#7 (Sin línea C ni línea T)",         "value": "result_7"},
    {"label": "N/A (control no disponible)",         "value": "na"},
]

MAPPING_NEG = json.dumps({
    "fixed_sample_type": "negative",
    "positions": [{"index": 0, "type": "select", "label": "Patrón Observado",
                   "instruction": "Seleccione el patrón visualizado.", "options": _OPTS}],
    "phrase_template": "Muestra negativa: Patrón {0}",
    "evaluation": {"rules": [
        {"sample_type": "negative", "result": "result_5", "verdict": "pass",
         "message": "Muestra Negativa: Patrón #5 — Visualización solo de línea control — CUMPLE"},
        *[{"sample_type": "negative", "result": f"result_{i}", "verdict": "fail",
           "message": f"Muestra Negativa: Patrón #{i} — NO CUMPLE"} for i in [1,2,3,4,6,7]],
        {"sample_type": "negative", "result": "na", "verdict": "not_applicable",
         "message": "Muestra Negativa: Control no disponible — N/A"},
    ]},
})

MAPPING_POS = json.dumps({
    "fixed_sample_type": "positive",
    "positions": [{"index": 0, "type": "select", "label": "Patrón Observado",
                   "instruction": "Seleccione el patrón visualizado.", "options": _OPTS}],
    "phrase_template": "Muestra positiva: Patrón {0}",
    "evaluation": {"rules": [
        *[{"sample_type": "positive", "result": f"result_{i}", "verdict": "pass",
           "message": f"Muestra Positiva: Patrón #{i} — Visualización línea control y línea de prueba — CUMPLE"}
          for i in [1,2,3,4]],
        *[{"sample_type": "positive", "result": f"result_{i}", "verdict": "fail",
           "message": f"Muestra Positiva: Patrón #{i} — NO CUMPLE"} for i in [5,6,7]],
        {"sample_type": "positive", "result": "na", "verdict": "not_applicable",
         "message": "Muestra Positiva: Control no disponible — N/A"},
    ]},
})

# ── MAVI-07 SpecConf ────────────────────────────────────────────────────────
# sc 84229 negativa  sc 84230 positiva
env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config
    SET evaluation_type='vama_multi_check',
        acceptance_criteria='Visualización solo de línea control, patrón #5',
        text_phrase_mapping=%s
    WHERE id=84229
""", (MAPPING_NEG,))

env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config
    SET evaluation_type='vama_multi_check',
        acceptance_criteria='Visualización línea control y línea de prueba, patrón #1-#4',
        text_phrase_mapping=%s
    WHERE id=84230
""", (MAPPING_POS,))
print("MAVI-07 SpecConf configurados")

# ── MAVI-09 SpecConf ────────────────────────────────────────────────────────
env.cr.execute("UPDATE amunet_quality_parameter_specification_config SET min_value=1,  max_value=30,  acceptance_criteria='1-30 segundos'   WHERE id=84231")
env.cr.execute("UPDATE amunet_quality_parameter_specification_config SET min_value=30, max_value=180, acceptance_criteria='30-180 segundos' WHERE id=84239")
print("MAVI-09 SpecConf configurados")

# ── Deactivar extra (sc 84228 combinado) ────────────────────────────────────
env.cr.execute("UPDATE amunet_quality_parameter_specification_config SET active=false WHERE id=84228")

# ── Anexo columnas en análisis 865 y 870 ────────────────────────────────────
COLS = {
    'anexo_titulo':      'Anexo Producto Terminado Cartucho',
    'anexo_col1_header': 'Apariencia de Empaque',
    'anexo_col2_header': 'Apariencia de Prueba',
    'anexo_col3_header': 'Hermeticidad',
    'anexo_col4_header': 'Contenido',
    'anexo_col5_header': 'T. Liberación (seg)',
    'anexo_col6_header': 'T. Migración (seg)',
    'anexo_col7_header': 'Desempeño',
    'anexo_col8_header': '',
}
for check_id in [865, 870]:
    sets = ', '.join(f"{k}=%s" for k in COLS)
    env.cr.execute(f"UPDATE amunet_quality_check SET {sets} WHERE id=%s",
                   (*COLS.values(), check_id))
print("Anexo Cartucho configurado en análisis 865 y 870")

env.cr.commit()
print("✓ Restauración completada — template PT Cualitativas DMHBA01")
