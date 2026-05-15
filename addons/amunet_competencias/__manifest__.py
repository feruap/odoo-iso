{
    'name': 'Amunet - Competencias y Capacitación (ISO 13485 §6.2)',
    'version': '19.0.4.0.0',
    'category': 'Quality',
    'summary': 'Cursos, exámenes, planes de estudio, matriz de competencias y bloqueo de firma por competencia vencida',
    'description': """
        Gestión de Capacitación bajo ISO 13485 Cláusula 6.2.

        Funcionalidades:
        - Cursos de capacitación: varios videos (reproductor embebido),
          material escrito, PDFs y examen.
        - Examen de opción múltiple con calificación almacenada, vigencia
          configurable, tiempo mínimo de estudio y tiempo límite de examen.
        - Autoservicio "Mis Cursos": cada empleado toma sus cursos y presenta
          el examen desde su propio usuario de Odoo.
        - Al aprobar un examen se genera automáticamente el registro de
          capacitación vigente para los PNOs del curso.
        - Planes de estudio por puesto/departamento y tablero de avance
          de capacitación del personal.
        - Cada equipo muestra los cursos que requiere (derivados de sus PNOs).
        - Alerta automática de revisión cuando cambia la versión de un PNO.
        - Matriz de competencias por usuario / SOP / Parámetro.
        - Bloqueo pre-PIN: impide firmar un control de calidad si la
          capacitación está vencida (configurable via parámetro de sistema).
    """,
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

        # Crons (alertas y reporte mensual)
        'data/cron_alertas.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
