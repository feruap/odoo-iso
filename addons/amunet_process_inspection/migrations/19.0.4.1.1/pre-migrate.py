# -*- coding: utf-8 -*-
"""Renombra las claves de la etapa de linea larga, quitando el prefijo L1-L4.

La numeracion (L1, L2, L3, L4) fue solo la forma de nombrar las lineas al
describirlas; no es como deben aparecer en el sistema (Mery, 08-sep-2026).

Las claves viejas alcanzaron a guardarse en staging, asi que el cambio de
etiqueta no basta: hay que mover el DATO. Si no, la orden queda con un valor
que ya no existe en la lista y el campo se ve vacio sin que nadie sepa por que.

En produccion no habia ninguna orden con etapa, asi que ahi no cambia nada.
"""

EQUIVALENCIAS = [
    ('l1_soluciones', 'soluciones'),
    ('l2_conjugados', 'conjugados'),
    ('l3_inyeccion', 'inyeccion'),
    ('l4_laminado', 'laminado'),
]


def migrate(cr, version):
    if not version:
        return

    cr.execute("""
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'mrp_production'
           AND column_name = 'amunet_sublinea'
    """)
    if not cr.fetchone():
        return

    total = 0
    for vieja, nueva in EQUIVALENCIAS:
        cr.execute(
            "UPDATE mrp_production SET amunet_sublinea = %s WHERE amunet_sublinea = %s",
            (nueva, vieja),
        )
        total += cr.rowcount

    # Las opciones viejas quedan huerfanas en el catalogo de selecciones si no
    # se retiran; Odoo las recrea correctas al cargar el campo.
    cr.execute("""
        DELETE FROM ir_model_fields_selection s
         USING ir_model_fields f
         WHERE s.field_id = f.id
           AND f.model = 'mrp.production'
           AND f.name = 'amunet_sublinea'
           AND s.value IN ('l1_soluciones', 'l2_conjugados', 'l3_inyeccion', 'l4_laminado')
    """)

    if total:
        cr.execute("SELECT 1")  # no-op: el log lo imprime el runner
