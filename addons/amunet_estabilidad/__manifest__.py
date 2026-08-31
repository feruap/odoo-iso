# -*- coding: utf-8 -*-
{
    'name': 'Amunet Estudios de Estabilidad',
    'version': '19.0.1.0.0',
    'summary': 'Estudios de estabilidad (ICH Q1A) con puntos de jalado, resultados y firma',
    'description': """
Estudios de estabilidad de producto (dispositivos médicos / IVD).

- Estudio versionado y aprobado (protocolo, condiciones, puntos de jalado).
- Generación automática de puntos pendientes (evidencia de omisiones).
- Resultados por parámetro con evaluación de conformidad (dentro/fuera de especificación).
- Conclusión de vida útil firmada electrónicamente.
- Inmutabilidad tras aprobar, log de auditoría append-only.
""",
    'author': 'Amunet',
    'category': 'Manufacturing/Quality',
    'license': 'LGPL-3',
    'depends': [
        'mail',
        'product',
        'amunet_quality',
        'amunet_documentos',
    ],
    'data': [
        'security/amunet_estabilidad_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/amunet_stability_views.xml',
        'views/report_stability.xml',
        'views/amunet_stability_audit_log_views.xml',
        'views/menus.xml',
        'wizard/amunet_stability_sign_wizard_views.xml',
    ],
    'application': True,
    'installable': True,
}
