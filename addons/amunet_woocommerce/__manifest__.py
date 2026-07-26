# -*- coding: utf-8 -*-

{
    'name': 'Amunet - Consulta y planeación WooCommerce',
    'summary': 'Consulta, validación y planeación WooCommerce ↔ Odoo (solo lectura hacia Woo)',
    'description': """Aplicación de consulta y planeación entre WooCommerce y Odoo.

Solo lectura hacia WooCommerce (GET) y carga manual de snapshots: la aplicación
nunca escribe en la tienda ni modifica inventarios, lotes, órdenes de
fabricación, controles de calidad, BOM ni presentaciones de Odoo.

- Mapeo auditable Woo ↔ Odoo con revisión manual (pendiente/confirmado/rechazado).
- Consulta de inventario Woo por snapshot y de inventario físico Odoo, con
  banderas "calculable" y razón cuando un dato no puede obtenerse.
- Capacidad de fabricación corta desde BOM activa y ubicación fuente.
- Perfiles de proceso largo por hoja maestra (equivalencias, rendimiento, merma).
- Importación idempotente del CSV de mapeo de SKU.
- Tres grupos: Consulta, Revisor y Administrador, con reglas multiempresa.""",
    'author': 'Amunet',
    'category': 'Inventory',
    'version': '19.0.3.0.0',
    'depends': [
        'mail',
        'stock',
        'mrp',
        'amunet_packaging_planning',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/woo_backend_views.xml',
        'views/woo_product_mapping_views.xml',
        'views/woo_stock_snapshot_views.xml',
        'views/woo_long_process_views.xml',
        'views/woo_sync_log_views.xml',
        'wizard/woo_mapping_import_wizard_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
