{
    'name': 'Amunet - Visibilidad de Empleados',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Restringe la visibilidad del menu raiz de Empleados (hr)',
    'description': """
Amunet - Visibilidad de Empleados
=================================

Sobreescribe la lista de grupos del menu raiz "Empleados" (hr.menu_hr_root)
para que NO sea visible al grupo base.group_user (Rol / Miembro). Asi
solo los usuarios con grupos de Recursos Humanos pueden ver la
aplicacion de Empleados en el AppSwitcher:

- Encargado: gestionar a todos los empleados (hr.group_hr_user)
- Administrador (hr.group_hr_manager)

Empaqueta el cambio para que sea persistente entre upgrades del modulo
'hr'. Sin este modulo, un 'odoo -u hr' restaurara el grupo Rol / Miembro
y todos los empleados internos veran la app de Empleados nuevamente.
""",
    'author': 'Amunet S.A. de C.V.',
    'website': 'https://www.amunet.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'hr',
    ],
    'data': [
        'data/menu_visibility.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
}
