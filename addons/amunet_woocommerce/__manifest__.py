# -*- coding: utf-8 -*-

{
    'name': 'Amunet - Consulta y planeación WooCommerce',
    'summary': 'Consulta, validación y planeación WooCommerce ↔ Odoo',
    'description': """Aplicación de consulta y planeación entre WooCommerce y Odoo.

Lectura del catálogo y carga manual de snapshots. Los revisores pueden editar
nombres y transferir fotografías de forma manual y auditada; cualquier
escritura hacia Woo requiere habilitación explícita y credenciales separadas.
La aplicación nunca sincroniza inventarios ni modifica lotes, órdenes de
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
    'version': '19.0.11.4.0',
    'depends': [
        'amunet_recepcion_materiales',
        'mail',
        'stock',
        'mrp',
        'amunet_packaging_planning',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/woo_stock_sync_security.xml',
        'views/woo_backend_views.xml',
        'views/woo_product_mapping_views.xml',
        'views/woo_stock_snapshot_views.xml',
        'views/woo_long_process_views.xml',
        'views/woo_sync_log_views.xml',
        'wizard/woo_mapping_import_wizard_views.xml',
        'views/woo_stock_sync_views.xml',
        'data/woo_stock_sync_cron.xml',
        'views/menu_views.xml',
        'data/entrega_pt_gracia.xml',
        'data/entrega_pt_secuencia.xml',
        'wizard/amunet_entrega_pt_wizard_views.xml',
        'views/amunet_entrega_pt_views.xml',
        'views/entrega_pt_columnas_views.xml',
        'views/entrega_pt_picking_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
