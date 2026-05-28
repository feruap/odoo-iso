# -*- coding: utf-8 -*-
from odoo import fields, models

DEPT_SELECTION = [
    ('GENERAL', 'General'),
    ('ACONDICIONADO 1', 'Acondicionado 1'),
    ('ACONDICIONADO 2', 'Acondicionado 2'),
    ('ALMACÉN DE MATERIA PRIMA', 'Almacén de Materia Prima'),
    ('ALMACÉN DE PRODUCTO TERMINADO', 'Almacén de Producto Terminado'),
    ('ALMACÉN TEMPORAL DE PRODUCTO TERMINADO', 'Almacén Temporal de PT'),
    ('CONTROL DE CALIDAD', 'Control de Calidad'),
    ('DESARROLLO', 'Desarrollo'),
    ('ENCARTUCHADO', 'Encartuchado'),
    ('ESTABILIDAD', 'Estabilidad'),
    ('INYECCIÓN', 'Inyección'),
    ('LAMINADO, SECADO Y CORTE', 'Laminado, Secado y Corte'),
    ('LECTURA Y PRETRATAMIENTO', 'Lectura y Pretratamiento'),
    ('PRODUCCIÓN DE DESARROLLO MOLECULAR', 'Producción de Desarrollo Molecular'),
    ('SOLUCIONES', 'Soluciones'),
    ('VALIDACIÓN', 'Validación'),
]


class AmunetQualityProcedureExt(models.Model):
    _inherit = 'amunet.quality.procedure'

    department = fields.Selection(
        DEPT_SELECTION,
        string='Subcategoría / Área',
        index=True,
        help='Área o subcategoría a la que pertenece este PNO dentro de la Documentación.')
