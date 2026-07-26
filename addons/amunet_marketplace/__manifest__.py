{
    'name': 'Amunet - Marketplace Interno',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Catalogo interno conectado con solicitudes de material, compras y almacen',
    'description': """
Marketplace Interno Amunet
==========================

Capa de catalogo interno sobre Solicitudes de Material.

Objetivos:

- Mostrar productos en formato catalogo para usuarios no tecnicos.
- Separar solicitudes generales de solicitudes ligadas a produccion.
- Reutilizar el flujo existente de amunet_material_request para surtido y recepcion.
- Permitir propuestas controladas de nuevos productos para alta posterior.
""",
    'author': 'Amunet S.A. de C.V.',
    'website': 'https://www.amunet.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'product',
        'purchase_stock',
        'mrp',
        'hr',
        'amunet_material_request',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/product_template_views.xml',
        'views/amunet_material_request_views.xml',
        'views/marketplace_product_proposal_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
}
