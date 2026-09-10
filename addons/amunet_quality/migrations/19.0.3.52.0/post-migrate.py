# -*- coding: utf-8 -*-
"""Migración 52.0 — Corrección masiva de análisis activos de pruebas rápidas cualitativas.

Corrige todos los análisis en estado draft/in_progress de los 54 productos
cualitativos que aún tienen la estructura vieja de 4 parámetros:
  MAVI-07 (seq=10) — Negativo/Positivo (mapping competitivo, incorrecto)
  MAVI-09 (seq=20) — Liberación/Migración (rangos en 0, incorrectos)
  MAVI-11 (seq=30) — Altura 6 u 8 cm (eliminar)
  MAVI-04 (seq=40) — Aspectos visuales (solo 3 specs, incompleto)

Destino — estructura estándar igual a TORCH (6 parámetros):
  seq=10  MAVI-04  Aspectos de Empaque   (5 specs: Polvo, Manchas, Rasgaduras, Deformidad, Letra)
  seq=15  MAVI-04  Aspectos de Prueba    (2 specs: Rasgaduras, Deformidad)
  seq=20  MGA-0486 Hermeticidad          (1 spec: Prueba de colorante)
  seq=30  MAVI-09  Flujo capilar         (2 specs: Liberación 1-30s, Migración 30-180s)
  seq=40  MAVI-07  vama_multi_check      (2 specs: negativa=patrón#5, positiva=patrón#1-4)
  seq=50  INC-002  Verificación contenido (1 spec)

Depende de la migración 51.0 (que configuró los rels y spec_configs del producto).
Análisis con datos capturados → se omiten y quedan registrados en el log.

IDs de parámetros (iguales en staging y producción):
  145 MAVI-04  Aspectos Visuales
   90 MGA-0486 Hermeticidad
   69 MAVI-09  Desempeño del tiempo de flujo capilar
   65 MAVI-07  Visualización de líneas "resultado base"
  149 INC-002  Verificación de contenido de empaque

Fuente de la clasificación: clasificacion_de_pruebas.xlsx — Diana Flores, sept 2026.
"""
import logging

_logger = logging.getLogger(__name__)


# ─── Productos cualitativos (todas las 54 pruebas de la lista de Diana) ────────
# La migración detecta datos automáticamente y salta los que los tengan
# (CA125=DMCAO01, Zika=DMZIK01 tienen datos en prod → se omiten vía log)
# TORCH=DMTOR02 ya tiene la estructura correcta → rel de 51.0 no existirá distinto
CUALITATIVOS = frozenset([
    'DMAFP01',   # AFP
    'DMCAO01',   # CA125 (tiene datos en prod → se saltará)
    'DMCAM01',   # CA 15-3
    'DMCAP01',   # CA 19-9
    'DMCAL01',   # CALPROTECTINA
    'DMCBR01',   # CAMPYLOBACTER
    'DMCAN01',   # Candida albicans
    'DMIAM01',   # Cardiac Combo Advanced
    'DMMCT01',   # CARDIAC COMBO
    'DMCHA01',   # CHAGAS IgG
    'DMCHI01',   # CHIKUNGUNYA IgG e IgM
    'DMCLAM01',  # CLAMIDIANET
    'DMDCZ01',   # COMBO MOSQUITO DENV/CHIKV/ZIKV
    'DMCRD01',   # COMBO RESPIRATORIO INFLUENZA A y B + SARS-COV-2 + RSV
    'DMENG01',   # Combo Entamoeba histolytica + Giardia lamblia
    'DMESC01',   # Combo Entamoeba histolytica + Salmonella typhi
    'DMSVI01',   # COMBO SIFILIS + VIH 1.2
    'DIAM-024',  # COVFLU-NET
    'DIAM-023',  # COVID 19 IgG/IgM
    'DIAM-025',  # COVINET saliva
    'DIAM-029',  # COVINET nasofaríngea
    'DMDEN01',   # DENGUE NET
    'DMDEN02',   # DENGUE IgG/IgM
    'DMDMD01',   # DÍMERO-D
    'DMHCG03',   # EMBARAZO (hCG) ORINA
    'DMHCG01',   # EMBARAZO (hCG) SSP
    'DMENT01',   # Entamoeba histolytica
    'DMSPN02',   # Estreptococo A
    'DMSPN01',   # Estreptococo B
    'DMFRE01',   # FACTOR REUMATOIDE
    'DMFFN01',   # Fibronectina fetal
    'DMGIA01',   # Giardia lamblia
    'DMHBA01',   # HEMOGLOBINA CUALITATIVA
    'DMHYP01',   # H. pylori anticuerpos IgG/IgM
    'DMHPY02',   # H. pylori (Ag) en heces
    'DMIAB01',   # FLUNET (Influenza A y B)
    'DMICR01',   # COMBO RESPIRATORIO (código anterior)
    'DMIGE01',   # IgE
    'DMHCG02',   # HCG NET
    'DMMON01',   # MONONUCLEOSIS
    'DMMYC01',   # Mycoplasma pneumoniae
    'DMPRO01',   # NT-proBNP
    'DMPSA02',   # PROSTATINET
    'DMRAV01',   # ROTADENET
    'DMVSR01',   # RSV NET
    'DMSAT01',   # Salmonella typhi (Ag)
    'DMSGF01',   # Shigella flexneri
    'DMSPO01',   # Streptococcus pneumoniae
    'DMTET01',   # TÉTANOS
    'DMTIF01',   # TIFOIDEA IgG/IgM
    'DMTSH01',   # TSH CUALITATIVA
    'DMTRF01',   # TRANSFERRINA / FOB
    'DMATB01',   # TUBERCULOSIS
    'DMVIH01',   # VIH 1.2
    'DMVIH02',   # VIH 4ta GENERACIÓN
    'DIAM-002',  # SIFILINET
    'DMZIK01',   # ZIKA COMBO (puede tener datos en prod → se saltará)
])


def _check_tiene_datos(cr, check_id):
    """True si algún detalle tiene resultado capturado."""
    cr.execute("""
        SELECT 1
        FROM amunet_quality_test_line_detail d
        JOIN amunet_quality_test_line l ON l.id = d.test_line_id
        WHERE l.check_id = %s
          AND (
            (d.result_binary_option IS NOT NULL AND d.result_binary_option != '')
            OR d.result_numeric IS NOT NULL
            OR (d.multi_check_results_json IS NOT NULL
                AND d.multi_check_results_json::text NOT IN ('{}', 'null', '{"0":null}', ''))
          )
        LIMIT 1
    """, (check_id,))
    return bool(cr.fetchone())


def _asegurar_prueba_specs(cr, rel_mavi04_id, uid):
    """Agrega las 2 specs de Prueba (seq=60/70) al rel MAVI-04 si no existen."""
    # Tomar specification_id de Rasgaduras (seq=30) y Deformidad (seq=40) del mismo rel
    cr.execute("""
        SELECT sequence, specification_id, specification_name,
               binary_option_pass, binary_option_fail, acceptance_criteria
        FROM amunet_quality_parameter_specification_config
        WHERE product_parameter_rel_id = %s AND sequence IN (30, 40)
        ORDER BY sequence
    """, (rel_mavi04_id,))
    rows = {r[0]: r for r in cr.fetchall()}

    for empaque_seq, prueba_seq in ((30, 60), (40, 70)):
        if empaque_seq not in rows:
            continue
        cr.execute("""
            SELECT 1 FROM amunet_quality_parameter_specification_config
            WHERE product_parameter_rel_id = %s AND sequence = %s
        """, (rel_mavi04_id, prueba_seq))
        if cr.fetchone():
            continue  # ya existe
        r = rows[empaque_seq]
        cr.execute("""
            INSERT INTO amunet_quality_parameter_specification_config
                (product_parameter_rel_id, specification_id, sequence, specification_name,
                 evaluation_type, binary_option_pass, binary_option_fail, acceptance_criteria,
                 min_value, max_value, active, create_uid, write_uid, create_date, write_date)
            VALUES (%s, %s, %s, %s, 'binary_selection', %s, %s, %s, 0, 0, true,
                    %s, %s, NOW(), NOW())
        """, (rel_mavi04_id, r[1], prueba_seq, r[2], r[3], r[4], r[5], uid, uid))


def _fix_analysis(cr, check_id, check_name, product_tmpl_id, uid):
    """Elimina la estructura vieja y recrea la estándar. Devuelve True si aplicó."""

    # ── Buscar los 5 rels del producto (creados por la migración 51.0) ──────────
    def get_rel(param_id):
        cr.execute("""
            SELECT id FROM amunet_quality_parameter_product_rel
            WHERE product_tmpl_id = %s AND parameter_id = %s AND active = true
            LIMIT 1
        """, (product_tmpl_id, param_id))
        row = cr.fetchone()
        return row[0] if row else None

    # IDs de parámetro (iguales en staging y prod)
    rel04  = get_rel(145)  # MAVI-04 Aspectos Visuales
    rel_mga = get_rel(90)  # MGA-0486
    rel09  = get_rel(69)   # MAVI-09
    rel07  = get_rel(65)   # MAVI-07
    rel_inc = get_rel(149) # INC-002

    if not all([rel04, rel_mga, rel09, rel07, rel_inc]):
        missing = [
            n for n, r in zip(
                ['MAVI-04', 'MGA-0486', 'MAVI-09', 'MAVI-07', 'INC-002'],
                [rel04, rel_mga, rel09, rel07, rel_inc]
            ) if not r
        ]
        _logger.warning(
            "52.0: %s (id=%d) — rels faltantes %s (¿corrió la 51.0?), saltando",
            check_name, check_id, missing
        )
        return False

    # ── Asegurar specs de Prueba en MAVI-04 ─────────────────────────────────────
    _asegurar_prueba_specs(cr, rel04, uid)

    # ── Eliminar estructura vieja ────────────────────────────────────────────────
    cr.execute("DELETE FROM amunet_quality_test_line_detail WHERE check_id = %s", (check_id,))
    cr.execute("DELETE FROM amunet_quality_test_line WHERE check_id = %s", (check_id,))

    # ── seq=10: MAVI-04 — Aspectos de Empaque (5 specs) ─────────────────────────
    cr.execute("""
        INSERT INTO amunet_quality_test_line
            (check_id, sequence, parameter_id, parameter_rel_id, code, name,
             detail_count, has_details, create_uid, write_uid, create_date, write_date)
        VALUES (%s, 10, 145, %s, 'MAVI-04', 'MAVI-04 — Aspectos de Empaque',
                5, true, %s, %s, NOW(), NOW())
        RETURNING id
    """, (check_id, rel04, uid, uid))
    tl_emp = cr.fetchone()[0]

    SUFIJO_EMP = {
        'Polvo': 'Polvo — Empaque',
        'Manchas y/o suciedad': 'Manchas y/o suciedad — Empaque',
        'Rasgaduras': 'Rasgaduras — Empaque',
        'Deformidad o deterioro': 'Deformidad o deterioro — Empaque',
        'Letra adecuada': 'Letra adecuada — Empaque',
    }
    cr.execute("""
        SELECT id, sequence, specification_id, specification_name,
               binary_option_pass, binary_option_fail, acceptance_criteria
        FROM amunet_quality_parameter_specification_config
        WHERE product_parameter_rel_id = %s AND sequence BETWEEN 10 AND 50
        ORDER BY sequence
    """, (rel04,))
    for sc_id, sc_seq, spec_id, spec_name, pv, fv, crit in cr.fetchall():
        nombre = SUFIJO_EMP.get(spec_name, spec_name + ' — Empaque')
        cr.execute("""
            INSERT INTO amunet_quality_test_line_detail
                (test_line_id, check_id, specification_config_id, specification_id,
                 sequence, name, evaluation_type,
                 binary_option_pass, binary_option_fail, expected_value_binary,
                 acceptance_criteria, min_value, max_value,
                 create_uid, write_uid, create_date, write_date)
            VALUES (%s,%s,%s,%s,%s,%s,'binary_selection',%s,%s,%s,%s,0,0,%s,%s,NOW(),NOW())
        """, (tl_emp, check_id, sc_id, spec_id, sc_seq, nombre, pv, fv, pv, crit, uid, uid))

    # ── seq=15: MAVI-04 — Aspectos de Prueba (2 specs) ──────────────────────────
    cr.execute("""
        INSERT INTO amunet_quality_test_line
            (check_id, sequence, parameter_id, parameter_rel_id, code, name,
             detail_count, has_details, create_uid, write_uid, create_date, write_date)
        VALUES (%s, 15, 145, %s, 'MAVI-04', 'MAVI-04 — Aspectos de Prueba',
                2, true, %s, %s, NOW(), NOW())
        RETURNING id
    """, (check_id, rel04, uid, uid))
    tl_pru = cr.fetchone()[0]

    SUFIJO_PRU = {
        'Rasgaduras': 'Rasgaduras — Prueba',
        'Deformidad o deterioro': 'Deformidad o deterioro — Prueba',
    }
    cr.execute("""
        SELECT id, sequence, specification_id, specification_name,
               binary_option_pass, binary_option_fail, acceptance_criteria
        FROM amunet_quality_parameter_specification_config
        WHERE product_parameter_rel_id = %s AND sequence IN (60, 70)
        ORDER BY sequence
    """, (rel04,))
    for sc_id, sc_seq, spec_id, spec_name, pv, fv, crit in cr.fetchall():
        nombre = SUFIJO_PRU.get(spec_name, spec_name + ' — Prueba')
        cr.execute("""
            INSERT INTO amunet_quality_test_line_detail
                (test_line_id, check_id, specification_config_id, specification_id,
                 sequence, name, evaluation_type,
                 binary_option_pass, binary_option_fail, expected_value_binary,
                 acceptance_criteria, min_value, max_value,
                 create_uid, write_uid, create_date, write_date)
            VALUES (%s,%s,%s,%s,%s,%s,'binary_selection',%s,%s,%s,%s,0,0,%s,%s,NOW(),NOW())
        """, (tl_pru, check_id, sc_id, spec_id, sc_seq, nombre, pv, fv, pv, crit, uid, uid))

    # ── seq=20: MGA-0486 — Hermeticidad (1 spec) ────────────────────────────────
    cr.execute("""
        SELECT id, specification_id, binary_option_pass, binary_option_fail, acceptance_criteria
        FROM amunet_quality_parameter_specification_config
        WHERE product_parameter_rel_id = %s ORDER BY sequence LIMIT 1
    """, (rel_mga,))
    row = cr.fetchone()
    if row:
        sc_id, spec_id, pv, fv, crit = row
        cr.execute("""
            INSERT INTO amunet_quality_test_line
                (check_id, sequence, parameter_id, parameter_rel_id, code, name,
                 detail_count, has_details, create_uid, write_uid, create_date, write_date)
            VALUES (%s, 20, 90, %s, 'MGA-0486', 'Hermeticidad', 1, true, %s, %s, NOW(), NOW())
            RETURNING id
        """, (check_id, rel_mga, uid, uid))
        tl_mga = cr.fetchone()[0]
        cr.execute("""
            INSERT INTO amunet_quality_test_line_detail
                (test_line_id, check_id, specification_config_id, specification_id,
                 sequence, name, evaluation_type,
                 binary_option_pass, binary_option_fail, expected_value_binary,
                 acceptance_criteria, min_value, max_value,
                 create_uid, write_uid, create_date, write_date)
            VALUES (%s,%s,%s,%s,10,'Prueba de colorante','binary_selection',
                    %s,%s,%s,%s,0,0,%s,%s,NOW(),NOW())
        """, (tl_mga, check_id, sc_id, spec_id, pv, fv, pv, crit, uid, uid))

    # ── seq=30: MAVI-09 — Flujo capilar (2 specs) ───────────────────────────────
    cr.execute("""
        SELECT id, sequence, specification_id, min_value, max_value
        FROM amunet_quality_parameter_specification_config
        WHERE product_parameter_rel_id = %s ORDER BY sequence
    """, (rel09,))
    sc09 = cr.fetchall()

    cr.execute("""
        INSERT INTO amunet_quality_test_line
            (check_id, sequence, parameter_id, parameter_rel_id, code, name,
             detail_count, has_details, create_uid, write_uid, create_date, write_date)
        VALUES (%s, 30, 69, %s, 'MAVI-09', 'Desempeño del tiempo de flujo capilar',
                %s, true, %s, %s, NOW(), NOW())
        RETURNING id
    """, (check_id, rel09, len(sc09), uid, uid))
    tl_09 = cr.fetchone()[0]

    NOMBRES_09 = ['Liberación de conjugado', 'Migración de conjugado']
    CRITERIOS_09 = ['1 a 30 segundos', '30 a 180 segundos']
    for idx, (sc_id, sc_seq, spec_id, min_v, max_v) in enumerate(sc09):
        nombre = NOMBRES_09[idx] if idx < 2 else f'Tiempo {idx + 1}'
        crit = CRITERIOS_09[idx] if idx < 2 else ''
        cr.execute("""
            INSERT INTO amunet_quality_test_line_detail
                (test_line_id, check_id, specification_config_id, specification_id,
                 sequence, name, evaluation_type, acceptance_criteria,
                 min_value, max_value, create_uid, write_uid, create_date, write_date)
            VALUES (%s,%s,%s,%s,%s,%s,'numeric_range',%s,%s,%s,%s,%s,NOW(),NOW())
        """, (tl_09, check_id, sc_id, spec_id, (idx + 1) * 10, nombre, crit, min_v, max_v, uid, uid))

    # ── seq=40: MAVI-07 — vama_multi_check (2 specs) ────────────────────────────
    # Cualitativa: negativa=patrón#5 (solo C), positiva=patrón#1-4 (C+T)
    # El text_phrase_mapping se toma de los spec_masters 628/629 directamente
    # (la migración 51.0 creó los spec_configs sin copiarlo, quedan vacíos)
    cr.execute("""
        SELECT id, text_phrase_mapping
        FROM amunet_quality_check_parameter_specification
        WHERE id IN (628, 629)
    """)
    master_mappings = {row[0]: row[1] for row in cr.fetchall()}

    cr.execute("""
        SELECT id, sequence, specification_id, specification_name
        FROM amunet_quality_parameter_specification_config
        WHERE product_parameter_rel_id = %s ORDER BY sequence
    """, (rel07,))
    sc07 = cr.fetchall()

    cr.execute("""
        INSERT INTO amunet_quality_test_line
            (check_id, sequence, parameter_id, parameter_rel_id, code, name,
             detail_count, has_details, create_uid, write_uid, create_date, write_date)
        VALUES (%s, 40, 65, %s, 'MAVI-07', 'Visualización de líneas "resultado base"',
                %s, true, %s, %s, NOW(), NOW())
        RETURNING id
    """, (check_id, rel07, len(sc07), uid, uid))
    tl_07 = cr.fetchone()[0]

    for sc_id, sc_seq, spec_id, spec_name in sc07:
        if spec_name and 'negati' in spec_name.lower():
            acceptance = 'Patrón #5 (Solo línea control, sin línea T)'
            multi_json = '{"0":"result_5"}'
        else:
            acceptance = 'Patrones #1-#4 (Línea T visible)'
            multi_json = '{"0":"result_4"}'
        # spec_id apunta al spec_master (628=negativa, 629=positiva)
        mapping = master_mappings.get(spec_id)
        cr.execute("""
            INSERT INTO amunet_quality_test_line_detail
                (test_line_id, check_id, specification_config_id, specification_id,
                 sequence, name, evaluation_type, acceptance_criteria,
                 multi_check_results_json, text_phrase_mapping,
                 min_value, max_value, create_uid, write_uid, create_date, write_date)
            VALUES (%s,%s,%s,%s,%s,%s,'vama_multi_check',%s,%s,%s,0,0,%s,%s,NOW(),NOW())
        """, (tl_07, check_id, sc_id, spec_id, sc_seq, spec_name,
              acceptance, multi_json, mapping, uid, uid))

    # ── seq=50: INC-002 — Verificación de contenido (1 spec) ────────────────────
    cr.execute("""
        SELECT id, specification_id, binary_option_pass, binary_option_fail, acceptance_criteria
        FROM amunet_quality_parameter_specification_config
        WHERE product_parameter_rel_id = %s ORDER BY sequence LIMIT 1
    """, (rel_inc,))
    row = cr.fetchone()
    if row:
        sc_id, spec_id, pv, fv, crit = row
        cr.execute("""
            INSERT INTO amunet_quality_test_line
                (check_id, sequence, parameter_id, parameter_rel_id, code, name,
                 detail_count, has_details, create_uid, write_uid, create_date, write_date)
            VALUES (%s, 50, 149, %s, 'INC-002', 'Verificación de contenido de empaque',
                    1, true, %s, %s, NOW(), NOW())
            RETURNING id
        """, (check_id, rel_inc, uid, uid))
        tl_inc = cr.fetchone()[0]
        cr.execute("""
            INSERT INTO amunet_quality_test_line_detail
                (test_line_id, check_id, specification_config_id, specification_id,
                 sequence, name, evaluation_type,
                 binary_option_pass, binary_option_fail, expected_value_binary,
                 acceptance_criteria, min_value, max_value,
                 create_uid, write_uid, create_date, write_date)
            VALUES (%s,%s,%s,%s,10,'Verificación de contenido de empaque','binary_selection',
                    %s,%s,%s,%s,0,0,%s,%s,NOW(),NOW())
        """, (tl_inc, check_id, sc_id, spec_id, pv, fv, pv, crit, uid, uid))

    # ── Activar Anexo PT Cartucho en la cabecera ─────────────────────────────────
    cr.execute("""
        UPDATE amunet_quality_check SET
            tiene_anexos       = true,
            is_material_con_anexo = false,
            anexo_titulo       = 'Anexo Producto Terminado Cartucho',
            anexo_col1_header  = 'Apariencia de Empaque',
            anexo_col2_header  = 'Apariencia de Prueba',
            anexo_col3_header  = 'Hermeticidad',
            anexo_col4_header  = 'Contenido',
            anexo_col5_header  = 'T. Liberación (seg)',
            anexo_col6_header  = 'T. Migración (seg)',
            anexo_col7_header  = 'Desempeño',
            total_parameters   = 6,
            parameters_pending = 6,
            write_date         = NOW()
        WHERE id = %s
    """, (check_id,))

    return True


def migrate(cr, version):
    uid = 1  # SUPERUSER — OK en migración, no hay sesión de usuario
    corregidos = 0
    con_datos = 0
    sin_rel = 0

    for code in sorted(CUALITATIVOS):
        # Buscar product_template por default_code
        cr.execute("""
            SELECT id FROM product_template WHERE default_code = %s LIMIT 1
        """, (code,))
        row = cr.fetchone()
        if not row:
            continue
        pt_id = row[0]

        # Análisis activos (draft o in_progress)
        cr.execute("""
            SELECT id, name FROM amunet_quality_check
            WHERE product_id = %s AND state IN ('draft', 'in_progress')
        """, (pt_id,))
        analyses = cr.fetchall()
        if not analyses:
            continue

        _logger.info("52.0: %s — %d análisis activos", code, len(analyses))

        for check_id, check_name in analyses:
            if _check_tiene_datos(cr, check_id):
                _logger.warning(
                    "52.0: %s (id=%d, %s) — tiene datos capturados, se omite (corrección manual)",
                    check_name, check_id, code
                )
                con_datos += 1
                continue

            ok = _fix_analysis(cr, check_id, check_name, pt_id, uid)
            if ok:
                corregidos += 1
                _logger.info("52.0:   → %s (id=%d) corregido a estructura estándar", check_name, check_id)
            else:
                sin_rel += 1

    _logger.info(
        "52.0: COMPLETADA — corregidos=%d | con_datos_omitidos=%d | sin_rels=%d",
        corregidos, con_datos, sin_rel
    )
