# -*- coding: utf-8 -*-
{
    'name': 'Amunet Bitácoras (Limpieza / Temperatura y Humedad)',
    'version': '19.0.1.0.0',
    'summary': 'Bitácoras digitales recurrentes con firma y trazabilidad ISO 13485',
    'description': """
Bitácoras digitales para fábrica paperless (dispositivos médicos).

Sustituye las bitácoras en papel de:
- Limpieza de áreas (recurrencia configurable por turno/día/semana/mes)
- Registro de temperatura y humedad por área (con límites de especificación)

Características reguladas (ISO 13485 / Cofepris):
- Plantillas versionadas y aprobadas (control de cambios).
- Generación automática de registros pendientes (evidencia de omisiones).
- Firma electrónica por PIN con significado de rol (capturó / revisó / aprobó).
- Snapshot + hash de los datos críticos al firmar (registro inmutable).
- Log de auditoría append-only.
- Flujo de desviación cuando hay fuera de especificación.
""",
    'author': 'Amunet',
    'category': 'Manufacturing/Quality',
    'license': 'LGPL-3',
    'depends': [
        'mail',
        'amunet_quality',
        'amunet_equipment_calibration',
        'amunet_documentos',
    ],
    'data': [
        'security/amunet_bitacoras_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/amunet_bitacora_template_views.xml',
        'views/amunet_bitacora_entry_views.xml',
        'views/amunet_bitacora_audit_log_views.xml',
        'views/menus.xml',
        'wizard/amunet_bitacora_sign_wizard_views.xml',
        'data/bitacora_templates_seed.xml',
    ],
    'application': True,
    'installable': True,
}
