# -*- coding: utf-8 -*-
"""Migracion 50.0 — configuracion de analisis para pruebas SEMICUANTITATIVAS.

Control de Calidad (Diana Flores) definio el 08-sep-2026 que parametros aplican
a un analisis de producto terminado de prueba rapida semicuantitativa, y Mery
confirmo que aplica a TODAS, no solo a PSA.

EL PROBLEMA QUE RESUELVE
  Hoy estos productos traen ~61 especificaciones activas, asi que cada analisis
  nace con mas de 60 renglones y hay que depurarlo A MANO lote por lote. Paso con
  el analisis QC/2026/00146 de PSA: nacio con 61 y se dejo en 12.

  Ojo: la configuracion de STAGING tampoco servia de molde. Tiene los mismos 24
  MAVI-09 y los VAMA-034/036/064/091, y MAVI-15 ni aparece. La estructura buena
  solo existia dentro de un analisis que Diana depuro a mano; de ahi se tomo.

QUE HACE
  Desactiva todo lo que no aplica y deja SOLO estos 13 renglones por producto:

    MAVI-04  'Aspectos de Empaque'  5  Polvo, Manchas, Rasgaduras,
                                       Deformidad, Letra adecuada
    MAVI-04  'Aspectos de Prueba'   2  Sin rasgaduras, Sin deformidad
    MAVI-09                         2  Liberacion y Migracion de conjugado
    MGA-0486                        1  Prueba de colorante
    INC-002                         1  Verificacion de contenido de empaque
    MAVI-15                         2  Control negativo, Control positivo

  MAVI-04 aparece DOS veces a proposito: las mismas especificaciones se evaluan
  sobre el empaque y sobre la prueba, con etiquetas distintas. El vinculo
  producto-parametro admite duplicados, asi que son dos bloques.

  NO se borra nada: se desactiva (active=False). Los analisis ya existentes
  apuntan a estas configuraciones con llave foranea RESTRICT, y ademas son
  registros regulados que no se destruyen.

  Los parametros y especificaciones se resuelven por CODIGO y NOMBRE, nunca por
  id fijo: los ids difieren entre bases y eso ya tumbo la migracion 49.0.

  LOS VALORES (opciones binarias, rangos, criterios) van EXPLICITOS aqui, tomados
  del analisis que Diana aprobo. No se heredan de la especificacion del catalogo
  porque varias estan incompletas en produccion: INC-002 no tiene opciones binarias
  --nace sin nada que seleccionar-- y MAVI-09 trae los rangos en 0-0 aunque su
  criterio diga '1 a 30 segundos'. Heredar de ahi habria replicado el hueco en los
  tres productos.
"""
import logging

_logger = logging.getLogger(__name__)

PRODUCTOS = ('DMPSA01', 'DMTSH02', 'DMFRT02')

# (codigo_parametro, nombre_del_parametro, etiqueta_del_bloque, secuencia,
#  [(nombre_de_la_especificacion, etiqueta_a_mostrar), ...])
ESTRUCTURA = [
    ('MAVI-04', 'Aspectos Visuales', 'Aspectos de Empaque', 10, [
        ('Polvo', 'Polvo — Empaque',
         {'binary_option_pass': 'Sin polvo', 'binary_option_fail': 'Con polvo',
          'acceptance_criteria': 'Sin polvo'}),
        ('Manchas y/o suciedad', 'Manchas y/o suciedad — Empaque',
         {'binary_option_pass': 'Sin manchas y/o suciedad',
          'binary_option_fail': 'Con manchas y/o suciedad',
          'acceptance_criteria': 'Sin manchas y/o suciedad'}),
        ('Rasgaduras', 'Rasgaduras — Empaque',
         {'binary_option_pass': 'Sin rasgaduras', 'binary_option_fail': 'Con rasgaduras',
          'acceptance_criteria': 'Sin rasgaduras'}),
        ('Deformidad o deterioro', 'Deformidad o deterioro — Empaque',
         {'binary_option_pass': 'Sin deformidad o deterioro',
          'binary_option_fail': 'Con deformidad o deterioro',
          'acceptance_criteria': 'Sin deformidad o deterioro'}),
        ('Letra adecuada', 'Letra adecuada — Empaque',
         {'binary_option_pass': 'Letra adecuada', 'binary_option_fail': 'Letra inadecuada',
          'acceptance_criteria': 'Letra adecuada'}),
    ]),
    ('MAVI-04', 'Aspectos Visuales', 'Aspectos de Prueba', 20, [
        ('Rasgaduras', 'Sin rasgaduras — Prueba',
         {'binary_option_pass': 'Sin rasgaduras', 'binary_option_fail': 'Con rasgaduras',
          'acceptance_criteria': 'Sin rasgaduras — Prueba'}),
        ('Deformidad o deterioro', 'Sin deformidad o deterioro — Prueba',
         {'binary_option_pass': 'Sin deformidad', 'binary_option_fail': 'Con deformidad',
          'acceptance_criteria': 'Sin deformidad o deterioro — Prueba'}),
    ]),
    ('MAVI-09', None, None, 30, [
        ('Liberación de conjugado', 'Liberación de conjugado',
         {'min_value': 1, 'max_value': 30,
          'acceptance_criteria': 'Liberación de conjugado: 1 a 30 segundos'}),
        ('Migración de conjugado', 'Migración de conjugado',
         {'min_value': 30, 'max_value': 180,
          'acceptance_criteria': 'Migración de conjugado: 30 a 180 segundos'}),
    ]),
    ('MGA-0486', None, None, 40, [
        ('Prueba de colorante', 'Prueba de colorante',
         {'binary_option_pass': 'Ausencia de colorante',
          'binary_option_fail': 'Presencia de colorante',
          'acceptance_criteria': 'Ausencia de colorante'}),
    ]),
    ('INC-002', None, None, 50, [
        ('Verificación de contenido de empaque', 'Verificación de contenido de empaque',
         {'binary_option_pass': 'Contenido coincide con el especificado en el manual vigente',
          'binary_option_fail': 'No coincide con contenido especificado en el manual vigente',
          'acceptance_criteria': ('Coincidencia con el contenido especificado en el manual '
                                  'vigente. Presencia del dispositivo de prueba y desecante '
                                  'en empaque primario.')}),
    ]),
    ('MAVI-15', None, None, 60, [
        ('Control negativo', 'Control negativo', {}),
        ('Control positivo', 'Control positivo', {}),
    ]),
]


def _parametro(cr, code, nombre):
    """Resuelve el parametro por codigo. MAVI-04 tiene CUATRO registros con ese
    mismo codigo y distinto nombre, por eso se acepta un nombre para desempatar."""
    if nombre:
        cr.execute("SELECT id FROM amunet_quality_check_parameter "
                   "WHERE code=%s AND name=%s", (code, nombre))
        f = cr.fetchall()
        if len(f) == 1:
            return f[0][0]
    cr.execute("SELECT id, name FROM amunet_quality_check_parameter WHERE code=%s", (code,))
    f = cr.fetchall()
    if not f:
        raise Exception("Migracion 50.0: no existe el parametro %s en esta base" % code)
    if len(f) > 1:
        raise Exception("Migracion 50.0: %s corresponde a %d parametros (%s); "
                        "hace falta el nombre para desempatar"
                        % (code, len(f), ', '.join('%s=%s' % x for x in f)))
    return f[0][0]


def _spec(cr, param_id, nombre):
    cr.execute("SELECT id FROM amunet_quality_check_parameter_specification "
               "WHERE parameter_id=%s AND name=%s ORDER BY id LIMIT 1", (param_id, nombre))
    f = cr.fetchone()
    if not f:
        raise Exception("Migracion 50.0: no existe la especificacion '%s' bajo el "
                        "parametro %s" % (nombre, param_id))
    return f[0]


def migrate(cr, version):
    if not version:
        return

    ph = ','.join(['%s'] * len(PRODUCTOS))
    cr.execute("SELECT id, default_code FROM product_template WHERE default_code IN (%s)" % ph,
               PRODUCTOS)
    productos = cr.fetchall()
    _logger.info("Migracion 50.0: %d productos semicuantitativos encontrados", len(productos))

    for tmpl_id, code in productos:
        # 1. Desactivar TODO lo que hay hoy
        cr.execute("""UPDATE amunet_quality_parameter_specification_config
                      SET active=false, write_date=NOW()
                      WHERE product_tmpl_id=%s AND active=true""", (tmpl_id,))
        n_off = cr.rowcount
        cr.execute("""UPDATE amunet_quality_parameter_product_rel
                      SET active=false, write_date=NOW()
                      WHERE product_tmpl_id=%s AND active=true""", (tmpl_id,))
        _logger.info("  %s: %d configuraciones desactivadas", code, n_off)

        # 2. Construir la estructura aprobada
        creadas = 0
        for p_code, p_nombre, etiqueta, seq, specs in ESTRUCTURA:
            param_id = _parametro(cr, p_code, p_nombre)
            display = etiqueta or p_code

            cr.execute("""SELECT id FROM amunet_quality_parameter_product_rel
                          WHERE product_tmpl_id=%s AND parameter_id=%s
                            AND display_name=%s""", (tmpl_id, param_id, display))
            f = cr.fetchone()
            if f:
                rel_id = f[0]
                cr.execute("""UPDATE amunet_quality_parameter_product_rel
                              SET active=true, sequence=%s, write_date=NOW()
                              WHERE id=%s""", (seq, rel_id))
            else:
                cr.execute("""INSERT INTO amunet_quality_parameter_product_rel
                        (product_tmpl_id, parameter_id, parameter_code, display_name,
                         sequence, active, create_date, write_date, create_uid, write_uid)
                        VALUES (%s,%s,%s,%s,%s,true,NOW(),NOW(),1,1) RETURNING id""",
                    (tmpl_id, param_id, p_code, display, seq))
                rel_id = cr.fetchone()[0]

            for i, (spec_nombre, mostrar, valores) in enumerate(specs, start=1):
                spec_id = _spec(cr, param_id, spec_nombre)
                cr.execute("""SELECT id FROM amunet_quality_parameter_specification_config
                              WHERE product_parameter_rel_id=%s AND specification_id=%s""",
                           (rel_id, spec_id))
                g = cr.fetchone()
                if g:
                    cr.execute("""UPDATE amunet_quality_parameter_specification_config
                                  SET active=true, specification_name=%s, sequence=%s,
                                      acceptance_criteria=COALESCE(%s, acceptance_criteria),
                                      binary_option_pass=COALESCE(%s, binary_option_pass),
                                      binary_option_fail=COALESCE(%s, binary_option_fail),
                                      min_value=COALESCE(%s, min_value),
                                      max_value=COALESCE(%s, max_value),
                                      write_date=NOW() WHERE id=%s""",
                               (mostrar, i * 10, valores.get('acceptance_criteria'),
                                valores.get('binary_option_pass'), valores.get('binary_option_fail'),
                                valores.get('min_value'), valores.get('max_value'), g[0]))
                else:
                    cr.execute("""SELECT evaluation_type, acceptance_criteria,
                                         binary_option_pass, binary_option_fail,
                                         min_value, max_value, text_phrase_mapping
                                  FROM amunet_quality_check_parameter_specification
                                  WHERE id=%s""", (spec_id,))
                    base = cr.fetchone()
                    cr.execute("""INSERT INTO amunet_quality_parameter_specification_config
                            (product_parameter_rel_id, specification_id, specification_name,
                             evaluation_type, acceptance_criteria, binary_option_pass,
                             binary_option_fail, min_value, max_value, text_phrase_mapping,
                             active, sequence, product_tmpl_id, parameter_id,
                             create_date, write_date, create_uid, write_uid)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,true,%s,%s,%s,
                                    NOW(),NOW(),1,1)""",
                        (rel_id, spec_id, mostrar, base[0],
                         valores.get('acceptance_criteria', base[1]),
                         valores.get('binary_option_pass', base[2]),
                         valores.get('binary_option_fail', base[3]),
                         valores.get('min_value', base[4]),
                         valores.get('max_value', base[5]),
                         base[6], i * 10, tmpl_id, param_id))
                creadas += 1

            cr.execute("""UPDATE amunet_quality_parameter_product_rel
                          SET active_spec_count = (
                              SELECT COUNT(*) FROM amunet_quality_parameter_specification_config
                              WHERE product_parameter_rel_id=%s AND active=true),
                              write_date=NOW()
                          WHERE id=%s""", (rel_id, rel_id))

        _logger.info("  %s: estructura aprobada con %d especificaciones", code, creadas)

    _logger.info("Migracion 50.0 completa.")
