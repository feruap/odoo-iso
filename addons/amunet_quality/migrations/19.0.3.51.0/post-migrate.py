# -*- coding: utf-8 -*-
"""Migracion 51.0 — configuracion de analisis para pruebas rapidas CUALITATIVAS.

Tercera y ultima familia. Las otras dos ya quedaron:
    49.0  PCR rapida (DL*)          12 especificaciones
    50.0  Semicuantitativas          13
    51.0  Cualitativas (esta)        11

EL PROBLEMA
  Los productos de esta familia traen entre 16 y 73 especificaciones activas, con
  un promedio de 47. Cada analisis nace con esa cantidad de renglones y hay que
  depurarlo A MANO lote por lote. Paso con ToRCH: nacio con 49 y se dejo en 11.

  Hacerlo producto por producto con SQL suelto no escala --y ademas no sobrevive
  a un clon de produccion ni a una reinstalacion del modulo, porque el SQL no
  viaja con el codigo. Por eso va como migracion.

LA ESTRUCTURA
  Es la que Control de Calidad definio y aplico en DMTOR02 (ToRCH), 11 renglones:

    MAVI-04   5  Polvo, Manchas, Rasgaduras, Deformidad, Letra adecuada
    MGA-0486  1  Prueba de colorante
    MAVI-09   2  Liberacion (1-30 s) y Migracion (30-180 s) de conjugado
    MAVI-07   2  Muestra negativa, Muestra positiva
    INC-002   1  Verificacion de contenido de empaque

  Se diferencia de las semicuantitativas en dos cosas: aqui la lectura del
  resultado es MAVI-07 (cualitativa) y no MAVI-15, y MAVI-04 va en un solo
  bloque, sin el de "Prueba".

DOS DEFECTOS DEL ARREGLO MANUAL QUE AQUI SE CORRIGEN
  El SQL que se corrio sobre ToRCH dejo dos cosas a medias:

  1. Los rangos de MAVI-09 se corrigieron en el ANALISIS pero no en la
     configuracion del producto, que se quedo en 0-0. El siguiente analisis
     habria nacido con el mismo defecto que ya arreglamos en PSA: cualquier
     valor capturado sale fuera de rango.

  2. Se renombro la OPCION de la especificacion "Sellado" a "Letra adecuada",
     dejando un renglon que se llama Sellado y cuya opcion de cumplimiento dice
     Letra adecuada. Aqui se usa la especificacion "Letra adecuada", que ya
     existe en el catalogo, en vez de disfrazar la de Sellado.

Los parametros y especificaciones se resuelven por CODIGO y NOMBRE, nunca por id
fijo: MAVI-04 tiene cuatro registros con el mismo codigo y los ids difieren entre
bases (eso tumbo la 49.0). Los valores van explicitos, no se heredan del
catalogo, porque varias especificaciones estan incompletas ahi.

NO borra nada: desactiva. Los analisis existentes referencian estas
configuraciones y son registros regulados.
"""
import logging

_logger = logging.getLogger(__name__)

CATEGORIA = 'Producto terminado / Pruebas rápidas inmunológicas'

# Productos que YA tienen su estructura y no se tocan: los semicuantitativos de
# la 50.0 y el ToRCH que Calidad ajusto a mano.
EXCLUIDOS = ('DMPSA01', 'DMTSH02', 'DMFRT02', 'DMTOR02')

# (codigo, nombre_del_parametro, etiqueta_del_bloque, secuencia,
#  [(nombre_de_la_especificacion, etiqueta_a_mostrar, valores), ...])
ESTRUCTURA = [
    ('MAVI-04', 'Aspectos Visuales', 'Aspectos Visuales', 10, [
        ('Polvo', 'Polvo',
         {'binary_option_pass': 'Sin polvo', 'binary_option_fail': 'Con polvo',
          'acceptance_criteria': 'Sin polvo'}),
        ('Manchas y/o suciedad', 'Manchas y/o suciedad',
         {'binary_option_pass': 'Sin manchas y/o suciedad',
          'binary_option_fail': 'Con manchas y/o suciedad',
          'acceptance_criteria': 'Sin manchas y/o suciedad'}),
        ('Rasgaduras', 'Rasgaduras',
         {'binary_option_pass': 'Sin rasgaduras', 'binary_option_fail': 'Con rasgaduras',
          'acceptance_criteria': 'Sin rasgaduras'}),
        ('Deformidad o deterioro', 'Deformidad o deterioro',
         {'binary_option_pass': 'Sin deformidad o deterioro',
          'binary_option_fail': 'Con deformidad o deterioro',
          'acceptance_criteria': 'Sin deformidad o deterioro'}),
        # La especificacion 'Letra adecuada' YA EXISTE en el catalogo. Se usa esa,
        # en vez de renombrarle la opcion a la de 'Sellado' como se hizo a mano.
        ('Letra adecuada', 'Letra adecuada',
         {'binary_option_pass': 'Letra adecuada', 'binary_option_fail': 'Letra inadecuada',
          'acceptance_criteria': 'Letra adecuada'}),
    ]),
    ('MGA-0486', None, 'Hermeticidad', 20, [
        ('Prueba de colorante', 'Prueba de colorante',
         {'binary_option_pass': 'Ausencia de colorante',
          'binary_option_fail': 'Presencia de colorante',
          'acceptance_criteria': 'Ausencia de colorante'}),
    ]),
    ('MAVI-09', None, 'Desempeño del tiempo de flujo capilar', 30, [
        # Los rangos van AQUI, en la configuracion. Corregirlos solo en el
        # analisis deja el defecto para el siguiente lote.
        ('Liberación de conjugado', 'Liberación de conjugado',
         {'min_value': 1, 'max_value': 30,
          'acceptance_criteria': 'Liberación de conjugado: 1 a 30 segundos'}),
        ('Migración de conjugado', 'Migración de conjugado',
         {'min_value': 30, 'max_value': 180,
          'acceptance_criteria': 'Migración de conjugado: 30 a 180 segundos'}),
    ]),
    ('MAVI-07', None, 'Visualización de líneas', 40, [
        ('Muestra negativa', 'Muestra negativa', {}),
        ('Muestra positiva', 'Muestra positiva', {}),
    ]),
    ('INC-002', None, 'Verificación de contenido de empaque', 50, [
        ('Verificación de contenido de empaque', 'Verificación de contenido de empaque',
         {'binary_option_pass': 'Contenido coincide con el especificado en el manual vigente',
          'binary_option_fail': 'No coincide con contenido especificado en el manual vigente',
          'acceptance_criteria': ('Coincidencia con el contenido especificado en el manual '
                                  'vigente. Presencia del dispositivo de prueba y desecante '
                                  'en empaque primario.')}),
    ]),
]


def _parametro(cr, code, nombre):
    """Resuelve el parametro por codigo. MAVI-04 tiene CUATRO registros con ese
    codigo y distinto nombre, por eso se acepta un nombre para desempatar."""
    if nombre:
        cr.execute("SELECT id FROM amunet_quality_check_parameter "
                   "WHERE code=%s AND name=%s", (code, nombre))
        f = cr.fetchall()
        if len(f) == 1:
            return f[0][0]
    cr.execute("SELECT id, name FROM amunet_quality_check_parameter WHERE code=%s", (code,))
    f = cr.fetchall()
    if not f:
        raise Exception("Migracion 51.0: no existe el parametro %s en esta base" % code)
    if len(f) > 1:
        raise Exception("Migracion 51.0: %s corresponde a %d parametros (%s); hace falta "
                        "el nombre para desempatar"
                        % (code, len(f), ', '.join('%s=%s' % x for x in f)))
    return f[0][0]


def _spec(cr, param_id, nombre):
    cr.execute("SELECT id FROM amunet_quality_check_parameter_specification "
               "WHERE parameter_id=%s AND name=%s ORDER BY id LIMIT 1", (param_id, nombre))
    f = cr.fetchone()
    if not f:
        raise Exception("Migracion 51.0: no existe la especificacion '%s' bajo el "
                        "parametro %s" % (nombre, param_id))
    return f[0]


def migrate(cr, version):
    if not version:
        return

    ph = ','.join(['%s'] * len(EXCLUIDOS))
    cr.execute("""
        SELECT pt.id, pt.default_code
          FROM product_template pt
          JOIN product_category pc ON pc.id = pt.categ_id
         WHERE pt.active
           AND pc.complete_name = %%s
           AND pt.default_code IS NOT NULL
           AND pt.default_code NOT IN (%s)
           AND EXISTS (SELECT 1 FROM amunet_quality_parameter_product_rel r
                        WHERE r.product_tmpl_id = pt.id AND r.active)
         ORDER BY pt.default_code
    """ % ph, (CATEGORIA,) + EXCLUIDOS)
    productos = cr.fetchall()
    _logger.info("Migracion 51.0: %d productos cualitativos por configurar", len(productos))

    for tmpl_id, code in productos:
        cr.execute("""UPDATE amunet_quality_parameter_specification_config
                      SET active=false, write_date=NOW()
                      WHERE product_tmpl_id=%s AND active=true""", (tmpl_id,))
        cr.execute("""UPDATE amunet_quality_parameter_product_rel
                      SET active=false, write_date=NOW()
                      WHERE product_tmpl_id=%s AND active=true""", (tmpl_id,))

        creadas = 0
        for p_code, p_nombre, etiqueta, seq, specs in ESTRUCTURA:
            param_id = _parametro(cr, p_code, p_nombre)
            display = etiqueta or p_code

            cr.execute("""SELECT id FROM amunet_quality_parameter_product_rel
                          WHERE product_tmpl_id=%s AND parameter_id=%s AND display_name=%s""",
                       (tmpl_id, param_id, display))
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
                                      product_tmpl_id=%s,
                                      acceptance_criteria=COALESCE(%s, acceptance_criteria),
                                      binary_option_pass=COALESCE(%s, binary_option_pass),
                                      binary_option_fail=COALESCE(%s, binary_option_fail),
                                      min_value=COALESCE(%s, min_value),
                                      max_value=COALESCE(%s, max_value),
                                      write_date=NOW() WHERE id=%s""",
                               (mostrar, i * 10, tmpl_id,
                                valores.get('acceptance_criteria'),
                                valores.get('binary_option_pass'),
                                valores.get('binary_option_fail'),
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

        _logger.info("  %s: %d especificaciones", code, creadas)

    _logger.info("Migracion 51.0 completa: %d productos.", len(productos))
