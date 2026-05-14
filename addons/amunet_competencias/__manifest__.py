{
    'name': 'Amunet - Competencias y Capacitación (ISO 13485 §6.2)',
    'version': '19.0.2.0.0',
    'category': 'Quality',
    'summary': 'Cursos, exámenes, matriz de competencias y bloqueo de firma por competencia vencida',
    'description': """
        Gestión de Capacitación bajo ISO 13485 Cláusula 6.2.

        Funcionalidades:
        - Cursos de capacitación: video, material escrito, PDFs y examen.
        - Examen de opción múltiple con calificación almacenada y vigencia
          configurable por curso.
        - Autoservicio "Mis Cursos": cada empleado toma sus cursos y presenta
          el examen desde su propio usuario de Odoo.
        - Al aprobar un examen se genera automáticamente el registro de
          capacitación vigente para los PNOs del curso.
        - Cada equipo muestra los cursos que requiere (derivados de sus PNOs).
        - Registros de capacitación con fecha de caducidad.
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
        'views/amunet_curso_views.xml',
        'views/amunet_curso_intento_views.xml',
        'views/amunet_mis_cursos_views.xml',
        'views/amunet_equipment_inherit_views.xml',

        # Vistas — Registros y matriz
        'views/amunet_registro_capacitacion_views.xml',
        'views/amunet_matriz_competencias_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
