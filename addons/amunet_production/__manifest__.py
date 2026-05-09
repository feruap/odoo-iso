{
    'name': "Amunet Módulo de Producción de Soluciones",
    'summary': """
        Módulo personalizado de producción y extensión del MRP (Soluciones).
    """,
    'description': """
        Extiende el flujo de Fabricación nativo para integrar:
        - Control especializado de parámetros bioquímicos/físicos (pH).
        - Extensión de recetas con validación estricta de caducidad y lotes por componente.
        - Candados de finalización dependientes del área de Calidad.
        - Emisión de reportes de finalización en formatos Zebra reducidos.
    """,
    'author': "Amunet",
    'category': 'Manufacturing',
    'version': '19.0.1.0.0',
    'depends': ['mrp', 'stock', 'amunet_quality'],
    'data': [
        'data/production_data.xml',
        'security/ir.model.access.csv',
        # 'security/production_security.xml',
        'wizard/amunet_analysis_wizard_views.xml',
        'reports/production_label_report.xml',
        'views/mrp_production_views.xml',
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
