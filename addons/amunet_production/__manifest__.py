{
    'name': "Amunet Módulo de Producción de Soluciones",
    'summary': """Módulo personalizado de producción y extensión del MRP.""",
    'description': """Extension MRP para Amunet.

- 19.0.1.1.0: M2M equipos en mrp.workcenter y control de calibracion vigente.
- 19.0.1.2.0: Validaciones fail-closed, estado activo y excepcion documentada.
- 19.0.1.3.0: Reporte MO con trazabilidad ISO 13485 / Cofepris.""",
    'author': "Amunet",
    'category': 'Manufacturing',
    'version': '19.0.1.35.1',
    'depends': [
        'mrp',
        'stock',
        'amunet_quality',
        'amunet_equipment_calibration',
        'amunet_material_request',
        'amunet_competencias',
    ],
    'data': [
        'data/production_data.xml',
        'data/iso_dashboard_data.xml',
        'data/system_parameters.xml',
        'security/amunet_production_security.xml',
        'security/ir.model.access.csv',
        'wizard/amunet_analysis_wizard_views.xml',
        'reports/production_label_report.xml',
        'reports/mrp_production_report.xml',
        'views/operator_workorder_views.xml',
        'views/amunet_lot_dossier_views.xml',
        'views/amunet_iso_dashboard_views.xml',
        'views/mrp_production_views.xml',
        'views/mrp_workcenter_views.xml',
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
