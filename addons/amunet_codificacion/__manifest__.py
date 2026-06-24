# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Codificación de productos',
    'version': '19.0.1.1.0',
    'category': 'Inventory',
    'summary': 'Normativa de claves de productos: catálogo de abreviaturas y registro/documentación',
    'description': """
Codificación de productos Amunet
================================
Fase 1: documentación visible de las claves.

- Catálogo de abreviaturas (clasificación MP/MI/SP/ST/PT + sub-categoría + abreviatura).
- Registro de claves de productos (la lista que se consulta y crece al dar de alta).

La generación automática de la clave y el aviso a Almacén se agregan en fases posteriores.
    """,
    'author': 'Amunet S.A. de C.V.',
    'website': 'https://www.amunet.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'product',
        'stock',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/abreviaturas_seed.xml',
        'data/mail_template_almacen.xml',
        'views/amunet_clave_views.xml',
        'views/product_codificacion_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
