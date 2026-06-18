# -*- coding: utf-8 -*-
{
    'name': 'Amunet Monitor de Temperatura',
    'version': '19.0.1.18.0',
    'summary': 'Captura rapida e interactiva de temperatura y humedad por area',
    'description': """
Monitor de Temperatura (control ambiental) — app interactiva estilo
"Mi produccion" para registrar temperatura y humedad por area, de forma
rapida y trazable.

- Tablero de tarjetas de los turnos pendientes de hoy, por area.
- Cada usuario ve solo las areas que le corresponden segun su DEPARTAMENTO
  y rol en Empleados (todo derivado: si cambia el empleado, cambia el acceso).
- Captura minima (temp + humedad + observacion) firmada con PIN.
- Fuera de rango: avisa al supervisor del area, que revisa y cierra.
- Cierre diario firmado por el supervisor -> registros inmutables.
- Instrumento (termohigrometro) por area, ligado a su calibracion.
""",
    'author': 'Amunet',
    'category': 'Manufacturing/Quality',
    'license': 'LGPL-3',
    'depends': [
        'hr',
        'mail',
        'amunet_equipment_calibration',
        'amunet_quality',
    ],
    'data': [
        'security/amunet_monitor_temperatura_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'wizards/amunet_temp_capture_wizard_views.xml',
        'wizards/amunet_temp_signoff_wizard_views.xml',
        'wizards/amunet_temp_chart_wizard_views.xml',
        'views/amunet_temp_reading_views.xml',
        'views/amunet_temp_area_views.xml',
        'views/menus.xml',
        'reports/amunet_temp_report.xml',
    ],
    'application': True,
    'installable': True,
    'post_init_hook': 'post_init_hook',
}
