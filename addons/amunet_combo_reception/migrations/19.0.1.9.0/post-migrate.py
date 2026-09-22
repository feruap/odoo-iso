# -*- coding: utf-8 -*-
"""Marca las lineas de combo que YA se convirtieron antes de existir la marca.

Sin esto la guarda no protege a los combos historicos: el proximo movimiento
del combo (la ruta a Control de calidad, un traslado manual) volveria a
disparar la conversion y a inventar lotes nuevos para las mismas hojas.

Se emparejan por el picking de origen, que la conversion deja escrito en su
propio `origin`: "Conversión combo AMP/IN/00346".
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        UPDATE stock_move_line ml
           SET amunet_combo_conv_id = conv.id
          FROM stock_picking conv
          JOIN stock_move cmv ON cmv.picking_id = conv.id
          JOIN product_product pp ON pp.id = cmv.product_id
          JOIN product_template pt ON pt.id = pp.product_tmpl_id
         WHERE conv.origin LIKE 'Conversión combo %%'
           AND pt.es_combo_compra = true
           AND ml.product_id = cmv.product_id
           AND ml.amunet_combo_conv_id IS NULL
           AND ml.picking_id IS NOT NULL
           AND ml.picking_id <> conv.id
           AND conv.origin = 'Conversión combo ' || (
                 SELECT p2.name FROM stock_picking p2 WHERE p2.id = ml.picking_id
               )
    """)
    _logger.info('amunet_combo_reception: %s lineas de combo marcadas como ya convertidas', cr.rowcount)
