# -*- coding: utf-8 -*-
{
    'name': 'Amunet Limpieza de Áreas',
    'version': '19.0.1.0.0',
    'summary': 'Bitácora de limpieza por área, súper simple: escanear QR + PIN. Rotación de sanitizante y firma del supervisor.',
    'description': """
Limpieza de áreas (PNOMA-002 / PNOPR-003 / PNOCC-006 / PNOEST-003 / PNOAL-003).

Diseñado para que el personal de limpieza (no técnico) haga lo mínimo:
- El sistema genera solo las tareas de cada área según su frecuencia.
- Sanitizante de la semana automático (rota Cloro/Cuaternario cada lunes).
- El responsable confirma con "Limpié" + PIN; el supervisor del área firma con PIN.
- Lo no hecho a tiempo queda "Omitido" y el supervisor marca qué pasó.

Reutiliza las áreas y el supervisor del Monitor de Temperatura, y el PIN de firmas
de Calidad. Sin duplicar configuración.
""",
    'author': 'Amunet',
    'category': 'Manufacturing/Quality',
    'license': 'LGPL-3',
    'depends': [
        'mail',
        'amunet_monitor_temperatura',
        'amunet_quality',
    ],
    'data': [
        'security/amunet_limpieza_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/limpieza_templates.xml',
        'views/amunet_limpieza_item_views.xml',
        'views/amunet_limpieza_tarea_views.xml',
        'wizard/amunet_limpieza_pin_wizard_views.xml',
        'views/menus.xml',
    ],
    'post_init_hook': '_amunet_limpieza_post_init',
    'application': True,
    'installable': True,
}
