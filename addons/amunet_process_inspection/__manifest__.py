# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Inspecciones de proceso',
    'version': '19.0.4.0.5',
    'category': 'Manufacturing',
    'summary': 'Inspecciones operativas durante el proceso productivo '
               '(ISO 13485 §8.2.5). NO sustituye la liberacion de lote.',
    'description': """
Amunet - Inspecciones de proceso
================================

Cubre las inspecciones que se realizan en cada estacion del flujo de
produccion (linea corta y linea larga):

* Inspeccion formal de Control de Calidad en estaciones criticas
  (Lotificado, Encartuchado, Almacen Temporal PT).
* Supervision operativa por el jefe / supervisor de produccion
  en estaciones donde el control es interno del area
  (Corte, Acondicionado 1, Sellado, Acondicionado 2).

Se diferencia del modulo amunet_quality (liberacion de lote, §8.2.6):
aqui solo se documenta el control DEL PROCESO, retirando piezas
no conformes sin rechazar el lote completo.

Folio: INP/MMAA/NNN con reinicio mensual.
""",
    'author': 'Amunet S.A. de C.V.',
    'website': 'https://www.amunet.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'mrp',
        'mail',
        'amunet_production',
        'amunet_lot',
        'amunet_pilot_preflight',
        'amunet_quality',
        'amunet_material_request',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/amunet_process_inspection_views.xml',
        'views/mrp_routing_workcenter_views.xml',
        'views/mrp_production_views.xml',
        'views/menu_views.xml',
        'views/aru_menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
