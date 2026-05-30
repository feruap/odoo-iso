{
    'name': 'Amunet - Competencias y Capacitación (ISO 13485 §6.2)',
    'version': '19.0.5.1.1',
    'category': 'Quality',
    'summary': 'Cursos, exámenes, planes de estudio, matriz de competencias y bloqueo de firma por competencia vencida',
    'description': """Gestion de Capacitacion bajo ISO 13485 Clausula 6.2.

Funcionalidades:

- Cursos de capacitacion con videos, material escrito, PDFs y examen.
- Examen de opcion multiple con calificacion, vigencia y tiempos configurables.
- Autoservicio Mis Cursos para empleados.
- Registro automatico de capacitacion vigente al aprobar.
- Planes de estudio por puesto/departamento y tablero de avance.
- Trazabilidad de cursos requeridos por equipo/PNO.
- Matriz de competencias por usuario, SOP y parametro.
- Bloqueo pre-PIN para firmas con capacitacion vencida.""",
    'author': 'DIC Consultores - Rafael López Flores',
    'website': 'https://www.amunet.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'amunet_quality',
        'amunet_equipment_calibration',
        'hr',
        'mail',
    ],
    'data': [
        # Seguridad
        'security/amunet_competencias_security.xml',
        'security/ir.model.access.csv',

        # Datos maestros
        'data/ir_sequence_data.xml',
        'data/res_config_params.xml',

        # Vistas — Cursos y exámenes
        'views/amunet_curso_video_views.xml',
        'views/amunet_curso_views.xml',
        'views/amunet_curso_intento_views.xml',
        'views/amunet_mis_cursos_views.xml',

        # Vistas — Planes de estudio y avance
        'views/amunet_plan_estudios_views.xml',
        'views/amunet_hr_employee_views.xml',

        # Vistas — Equipos, registros y matriz
        'views/amunet_equipment_inherit_views.xml',
        'views/amunet_registro_capacitacion_views.xml',
        'views/amunet_matriz_competencias_views.xml',
        'views/menus.xml',
        'views/amunet_hr_workqueue_views.xml',

        # Crons (alertas y reporte mensual)
        'data/cron_alertas.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
