# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Control de Acceso N3000',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Tarjetas de acceso y codigo QR de la puerta (N3000) desde RRHH',
    'description': """
Amunet - Control de Acceso N3000
================================

Agrega al empleado (hr.employee) los datos del control de acceso de la puerta
(sistema N3000):

* Numero de tarjeta de acceso
* Codigo QR generado a partir del numero de tarjeta, para que RRHH lo comparta
  con el empleado (el empleado lo muestra a la camara para entrar).
* Habilitacion y vigencia del acceso.

Visible solo para usuarios de Recursos Humanos.
""",
    'author': 'Amunet S.A. de C.V.',
    'website': 'https://www.amunet.com.mx',
    'license': 'LGPL-3',
    'depends': ['hr'],
    'data': [
        'views/hr_employee_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
