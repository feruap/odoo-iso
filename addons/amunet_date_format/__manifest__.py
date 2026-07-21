# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Fecha con año siempre visible',
    'version': '19.0.1.0.0',
    'summary': 'Muestra siempre el año en los campos de fecha (dd.mm.yy), '
               'anulando la conducta de Odoo 19 que oculta el año en curso.',
    'description': """
Odoo 19 muestra los campos de fecha del anio en curso en formato condensado
sin anio (ej. "1 jun"), dejando el anio completo solo en el tooltip. En un
entorno regulado (ISO 13485 / Cofepris) las fechas no deben ser ambiguas.

Este modulo parchea el componente DateTimeField (y su variante de lista) para
que el valor mostrado use siempre el formato completo del idioma, que en
Amunet esta configurado como %d.%m.%y (ej. 01.06.26), con anio siempre.
""",
    'category': 'Tools',
    'author': 'Amunet',
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            'amunet_date_format/static/src/date_year_patch.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
