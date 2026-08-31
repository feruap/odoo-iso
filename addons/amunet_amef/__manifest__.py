# -*- coding: utf-8 -*-
{
    'name': 'Amunet AMEF / Gestión de Riesgos (ISO 14971)',
    'version': '19.0.1.0.0',
    'summary': 'Análisis de riesgo (AMEF/FMEA) versionado, firmado y trazable',
    'description': """
Gestión de riesgo de dispositivos médicos (ISO 14971) en Odoo.

- Análisis de riesgo (AMEF) versionado y aprobado (control de cambios).
- Líneas de modo de falla con severidad/ocurrencia/detección, RPN y nivel de riesgo.
- Riesgo residual tras acciones (S/O/D nuevos).
- Firma electrónica por PIN (revisa / aprueba) e inmutabilidad tras aprobar.
- Log de auditoría append-only.
- Vínculo a PNO / documento controlado.
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
        'security/amunet_amef_security.xml',
        'security/ir.model.access.csv',
        'views/amunet_amef_views.xml',
        'views/amunet_amef_audit_log_views.xml',
        'views/menus.xml',
        'wizard/amunet_amef_sign_wizard_views.xml',
    ],
    'application': True,
    'installable': True,
}
