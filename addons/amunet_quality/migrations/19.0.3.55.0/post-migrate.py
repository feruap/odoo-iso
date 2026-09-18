# -*- coding: utf-8 -*-
"""Blinda el campo `active` de las tablas de calidad contra el NULL.

EL PROBLEMA QUE CIERRA
El 18-sep-2026 se encontraron 211 especificaciones y 11 parametros con
`active` en NULL. Odoo trata NULL como "no activo", asi que esos registros
EXISTIAN con sus valores correctos pero NO aparecian en el analisis: el
bloque salia vacio y nadie se enteraba.

Se crearon asi por cargas masivas via SQL directo, que se salta el
default=True del modelo (150 el 11-ago, 140 el 12-ago, 60 el 17-ago, 14 el
02-sep). Alcanzo a 45 productos y dejo 24 analisis CERRADOS aprobados sin un
control que si estaba configurado.

Mientras la columna admita NULL sin default, la proxima carga por SQL vuelve
a dejar registros invisibles. Esta migracion normaliza los que queden y pone
DEFAULT true + NOT NULL para que el motor mismo lo impida.
"""
import logging

_logger = logging.getLogger(__name__)

TABLAS = (
    'amunet_quality_parameter_specification_config',
    'amunet_quality_parameter_product_rel',
    'amunet_quality_point',
    'amunet_quality_check',
)


def migrate(cr, version):
    if not version:
        return
    for tabla in TABLAS:
        cr.execute("SELECT to_regclass(%s)", (tabla,))
        if not cr.fetchone()[0]:
            _logger.info("blindaje active: %s no existe, se omite", tabla)
            continue

        # 1. Normalizar lo que quede en NULL. Un NULL aqui nunca fue una
        #    decision: es un registro que se quiso crear activo y quedo mudo.
        cr.execute("UPDATE %s SET active = true WHERE active IS NULL" % tabla)
        if cr.rowcount:
            _logger.warning(
                "blindaje active: %s tenia %s registro(s) en NULL, activados",
                tabla, cr.rowcount)

        # 2. Cerrar la puerta en el motor.
        cr.execute("ALTER TABLE %s ALTER COLUMN active SET DEFAULT true" % tabla)

        # SAVEPOINT y no rollback: un rollback completo revertiria tambien los
        # UPDATE de las tablas ya procesadas en esta misma transaccion.
        cr.execute("SAVEPOINT blindaje_%s" % tabla)
        try:
            cr.execute("ALTER TABLE %s ALTER COLUMN active SET NOT NULL" % tabla)
        except Exception as exc:
            cr.execute("ROLLBACK TO SAVEPOINT blindaje_%s" % tabla)
            _logger.error(
                "blindaje active: no se pudo poner NOT NULL en %s (%s); "
                "el DEFAULT true si quedo aplicado", tabla, exc)
        else:
            cr.execute("RELEASE SAVEPOINT blindaje_%s" % tabla)
            _logger.info("blindaje active: %s -> DEFAULT true + NOT NULL", tabla)
