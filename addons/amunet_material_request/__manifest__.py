{
    'name': 'Amunet - Solicitudes de Material',
    'version': '19.0.1.4.3',
    'category': 'Inventory/Inventory',
    'summary': 'Solicitudes internas de material con trazabilidad de lotes',
    'description': """
Solicitudes de Material
=======================

Permite que cualquier usuario autorizado solicite material al almacen.

Flujo:

- Solicitante crea solicitud, indica productos y cantidades.
- El sistema valida stock disponible al enviar.
- Almacen recibe, asigna lote a cada linea y confirma la entrega.
- El stock se descuenta del almacen origen y se considera consumido.
- Quedan registradas las firmas digitales del solicitante y del almacenista.
""",
    'author': 'Amunet S.A. de C.V.',
    'website': 'https://www.amunet.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'stock',
        'mrp',
        'hr',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/ir_sequence_data.xml',
        'data/stock_location_data.xml',
        'views/amunet_material_request_views.xml',
        'views/res_users_views.xml',
        'views/hr_department_views.xml',
        'views/menu_views.xml',
        'reports/material_request_report.xml',
        'reports/material_request_report_template.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
