# -*- coding: utf-8 -*-
{
    'name': 'Mi produccion',
    'version': '19.0.1.8.0',
    'category': 'Manufacturing',
    'summary': 'Control de piso por actividad: el operador da clic en '
               'Inicia / Pausa / Termina por lote; alimenta la orden en '
               'tiempo real y permite la supervision por actividad.',
    'description': """
Mi produccion
=============

App de piso, separada del modulo de produccion. El personal de
produccion trabaja sus actividades por lote (Inicia / Pausa / Termina)
y la informacion se refleja en tiempo real en la orden de fabricacion,
para que supervisores y administracion la vean en vivo.

- Pantalla del OPERADOR: su lote, su actividad, botones grandes.
- MONITOR del supervisor: todos los lotes en tiempo real + firma de
  supervision por actividad.
- 19.0.1.8.0: MI DIA por puesto. Cada empleado tiene sus estaciones
  (hr.employee.amunet_mi_workcenter_ids); la pantalla del operador solo
  muestra las actividades de sus estaciones, ordenadas por fecha planeada
  del lote, incluyendo las bloqueadas (en espera del paso anterior).

No modifica el codigo del modulo de produccion; opera sobre las mismas
ordenes de trabajo (workorders).
""",
    'author': 'Amunet',
    'depends': [
        'mrp',
        'amunet_production',
        'amunet_process_inspection',
        'hr',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/amunet_mi_supervision_wizard_views.xml',
        'views/mi_produccion_views.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
