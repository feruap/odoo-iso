{
    'name': 'Amunet - Tablero de Actividades de Calidad',
    'version': '19.0.1.0.10',
    'summary': 'Reparto y priorizacion del trabajo de los analistas de Control de Calidad',
    'description': """
Tablero de actividades de Control de Calidad
============================================

Agrega la capa de PLANEACION sobre el analisis que ya existe (amunet.quality.check),
sin crear un modelo nuevo y sin duplicar informacion.

- El supervisor (Diana) asigna analista y fecha planeada.
- La prioridad se calcula sola:
    1. Bloquea produccion o venta
    2. Proximo a caducar o usar
    3. Normal
- Aviso (no bloqueo) si el analista no tiene capacitacion vigente.
  A partir de la fecha del parametro 'amunet_calidad_tablero.capacitacion_bloqueo_desde'
  el aviso se convierte en bloqueo.
""",
    'author': 'Amunet',
    'category': 'Quality',
    'license': 'LGPL-3',
    'depends': [
        'amunet_quality',
        'mrp',
        'stock',
    ],
    'data': [
        'data/ir_config_parameter.xml',
        'views/amunet_quality_check_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
