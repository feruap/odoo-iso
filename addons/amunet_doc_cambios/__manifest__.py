{
    'name': 'Amunet — Reportar cambios al instructivo desde producción',
    'version': '19.0.3.0.0',
    'category': 'Quality',
    'summary': 'Botón en la orden de fabricación para reportar cambios que puedan impactar el instructivo de uso',
    'author': 'Amunet',
    'depends': ['mail', 'mrp', 'amunet_change_control'],
    'data': [
        'security/ir.model.access.csv',
        'views/reporte_cambio_wizard_views.xml',
        'views/mrp_production_views.xml',
        'views/doc_revision_alert_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
