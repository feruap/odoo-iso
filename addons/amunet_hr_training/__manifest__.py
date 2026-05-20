{
    'name': 'Amunet - Capacitaciones HR (SGC)',
    'version': '19.0.2.0.0',
    'category': 'Human Resources',
    'summary': 'Programacion y control de capacitaciones bajo SGC con doble '
               'aprobacion (ponente + RH), invitaciones automaticas y alertas.',
    'description': """
Amunet - Capacitaciones HR (SGC)
================================

Submodulo de Recursos Humanos que cubre el ciclo completo de una
capacitacion bajo el Sistema de Gestion de Calidad:

- Modelo principal `hr.training.course`: nombre, ponente, fechas de
  inicio/fin, estado (Borrador / Confirmado / Realizado / Cancelado),
  participantes.
- Modelo `hr.training.attendance`: pase de lista por empleado, asistencia,
  puntualidad y calificacion final.
- Aprobacion en dos pasos: el ponente confirma + RH aprueba; cuando
  ambos confirman, el curso pasa a estado Confirmado.
- Invitaciones automaticas por correo a los participantes cuando el
  curso queda Confirmado.
- Cron diario: si el curso esta en Borrador y faltan exactamente 7
  dias para la fecha de inicio, se crea una actividad para el grupo
  de RH y se envia recordatorio al ponente.
- Notificacion automatica al cambiar fechas de un curso ya
  Confirmado, al ponente y a todos los participantes.
""",
    'author': 'Amunet S.A. de C.V.',
    'website': 'https://www.amunet.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'hr',
        'mail',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        'data/cron_data.xml',
        'views/hr_training_course_views.xml',
        'views/training_attend_templates.xml',
        'views/menu_views.xml',
    ],
    'external_dependencies': {
        'python': ['qrcode'],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
