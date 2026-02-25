# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Control de Calidad',
    'version': '19.0.3.2.8',
    'category': 'Quality',
    'summary': 'Sistema de Control de Calidad con Parámetros Jerárquicos',
    'description': """
        Sistema completo de Control de Calidad para la manufactura de dispositivos médicos
        y productos farmacéuticos.
    """,
    'author': 'DIC Consultores - Rafael López Flores',
    'website': 'https://www.amunet.com.mx',
    'license': 'LGPL-3',
    'icon': '/amunet_quality/static/description/icon.png',
    'depends': [
        'base',
        'stock',
        'purchase_stock',
        'product',
        'uom',
        'mail',
        'amunet_lot',
    ],
    'data': [
        # Seguridad y Datos Maestros
        'security/amunet_quality_security.xml',
        'security/ir.model.access.csv',

        # Menús (FUNDAMENTAL: Padrs primero para evitar iconos sueltos)
        'views/menu_parents.xml',

        # Data
        'data/ir_sequence_data.xml',
        'data/amunet_quality_additional_info_data.xml',
        'data/amunet_quality_parameters_data.xml',

        # Wizards
        'wizard/amunet_quality_reanalysis_wizard_views.xml',
        'wizard/amunet_quality_signature_wizard_views.xml',

        # Vistas de Modelos
        'views/amunet_quality_procedure_views.xml',
        'views/amunet_quality_capa_views.xml',
        'views/amunet_quality_supplier_audit_views.xml',
        'views/res_partner_views.xml',
        'views/amunet_quality_parameter_views.xml',
        'views/amunet_quality_point_views.xml',
        'views/amunet_quality_additional_info_views.xml',
        'views/amunet_quality_check_views.xml',
        'views/amunet_quality_signature_pin_views.xml',
        'views/res_users_views.xml',
        'views/product_template_views.xml',
        'views/stock_picking_views.xml',
        'views/purchase_order_views.xml',
        'views/amunet_quality_tecno_standalone_views.xml',

        # Menús (Hijos)
        'views/menus.xml',
        
        # Reportes
        'reports/quality_certificate_report.xml',
        'reports/solicitud_reporte_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'amunet_quality/static/src/js/mga0981_widget.js',
            'amunet_quality/static/src/js/vama034_widget.js',
            'amunet_quality/static/src/js/vama_multi_check_widget.js',
            'amunet_quality/static/src/js/quality_test_line_hierarchy.js',
            'amunet_quality/static/src/js/dynamic_placeholder_field.js',
            'amunet_quality/static/src/js/mavi07_widget.js',
            'amunet_quality/static/src/js/multi_condition_widget.js',
            'amunet_quality/static/src/js/vama044_widget.js',
            'amunet_quality/static/src/js/vama112_widget.js',
            'amunet_quality/static/src/js/vama078_widget.js',
            'amunet_quality/static/src/js/decision_matrix_widget.js',
            
            'amunet_quality/static/src/xml/mga0981_widget.xml',
            'amunet_quality/static/src/xml/vama034_widget.xml',
            'amunet_quality/static/src/xml/vama_multi_check_widget.xml',
            'amunet_quality/static/src/xml/quality_test_line_hierarchy.xml',
            'amunet_quality/static/src/xml/dynamic_placeholder_field.xml',
            'amunet_quality/static/src/xml/mavi07_widget.xml',
            'amunet_quality/static/src/xml/multi_condition_widget.xml',
            'amunet_quality/static/src/xml/vama044_widget.xml',
            'amunet_quality/static/src/xml/vama112_widget.xml',
            'amunet_quality/static/src/xml/vama078_widget.xml',
            'amunet_quality/static/src/xml/decision_matrix_widget.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
