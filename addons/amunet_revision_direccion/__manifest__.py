# -*- coding: utf-8 -*-
{
    'name': 'Amunet Revisión por la Dirección (ISO 13485 §5.6)',
    'version': '19.0.1.0.0',
    'summary': 'Revisión por la dirección: entradas, acuerdos/acciones y firma',
    'description': """
Revisión por la dirección conforme a ISO 13485 cláusula 5.6:
entradas (auditorías, quejas/retroalimentación, desempeño de procesos, estado de CAPA,
seguimiento de revisiones previas, cambios, recomendaciones de mejora), acuerdos y acciones
con responsable, fecha objetivo y enlace a CAPA, conclusión y firma electrónica.
""",
    'author': 'Amunet',
    'category': 'Manufacturing/Quality',
    'license': 'LGPL-3',
    'depends': ['mail', 'amunet_quality', 'amunet_documentos'],
    'data': [
        'security/amunet_revision_security.xml',
        'security/ir.model.access.csv',
        'views/amunet_management_review_views.xml',
        'views/menus.xml',
        'wizard/amunet_review_sign_wizard_views.xml',
    ],
    'application': True,
    'installable': True,
}
