# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Control de acceso dinámico por almacén',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Warehouse',
    'summary': 'Sistema de control de acceso granular a almacenes y operaciones de inventario',
    'description': """
Control de acceso dinámico por almacén
========================================

Este módulo implementa un sistema de control de acceso granular que permite:

* Asignar almacenes específicos a usuarios desde la interfaz gráfica
* Configurar acceso completo o restringido por tipo de operación
* Generar reglas de registro (Record Rules) automáticamente
* Validar permisos en backend para seguridad adicional
* Vista de matriz para gestión masiva de accesos

Características principales
----------------------------
* **Configuración gráfica**: Sin necesidad de código XML para cambios
* **Granularidad**: Control por almacén y tipo de operación
* **Seguridad backend**: Validaciones adicionales más allá de Record Rules
* **Auditoría**: Visibilidad completa de quién tiene acceso a qué
* **Cumplimiento normativo**: Separación de responsabilidades por área

Casos de uso
------------
- Restringir usuarios de recepción solo a operaciones de entrada
- Limitar acceso de Producción solo a almacenes específicos
- Evitar que usuarios accedan a almacenes fuera de su área
- Separar responsabilidades entre materias primas y producto terminado

    """,
    'author': 'Amunet S.A. de C.V.',
    'website': 'https://www.amunet.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'stock',
        'base',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',

        # Data (grupos, reglas se crean programáticamente)
        'data/amunet_warehouse_access_data.xml',

        # Views
        'views/amunet_warehouse_access_views.xml',
        'views/res_users_views.xml',
        'views/stock_warehouse_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
