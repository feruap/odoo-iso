# Marca como noupdate TODOS los xmlid de ir.sequence de los modulos amunet_*.
#
# Por que: varios modulos declaraban su secuencia de folios en un <data> sin
# noupdate="1" y con number_next=1. Cada `odoo -u` reescribia number_next=1 y
# reiniciaba el folio (en produccion ya hay PREF/2026/00006, 00008, 00019,
# 00025 y 00026 duplicados). Corregir el XML no basta: Odoo no actualiza la
# bandera noupdate de un xmlid que ya existe (ON CONFLICT solo toca
# model/res_id), asi que se corrige aqui por SQL, una sola vez.
#
# Vive en amunet_rework_control porque el NCR fue el primer folio afectado
# que se detecto; el UPDATE cubre todos los modulos amunet_* de golpe.
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute(
        """
        UPDATE ir_model_data
           SET noupdate = TRUE
         WHERE model = 'ir.sequence'
           AND module LIKE 'amunet%%'
           AND noupdate IS DISTINCT FROM TRUE
        """
    )
    _logger.info(
        "amunet_rework_control 19.0.1.0.2: %s secuencias amunet_* marcadas noupdate",
        cr.rowcount,
    )
