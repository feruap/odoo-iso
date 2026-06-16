# -*- coding: utf-8 -*-
{
    'name': 'Amunet Despeje de Línea',
    'version': '19.0.1.0.0',
    'summary': 'Despeje del área o línea de fabricación con checklist y firma (PNOPR-001)',
    'description': """
Despeje de línea/área de fabricación (PNOPR-001) digital:
checklist de verificación de que el área quedó libre del lote anterior, con firma electrónica
por PIN e inmutabilidad tras la firma. Reemplaza el formato de despeje en papel.
""",
    'author': 'Amunet',
    'category': 'Manufacturing/Quality',
    'license': 'LGPL-3',
    'depends': ['mail', 'amunet_quality'],
    'data': [
        'security/amunet_despeje_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/amunet_despeje_views.xml',
        'views/menus.xml',
        'wizard/amunet_despeje_sign_wizard_views.xml',
    ],
    'application': True,
    'installable': True,
}
