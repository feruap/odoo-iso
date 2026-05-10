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
        - (19.0.1.1.0) Vinculación formal de equipos Amunet a centros de trabajo
          (mrp.workcenter) con validación de calibración vigente al iniciar
          cada orden de trabajo.
        - (19.0.1.2.0) Fail-closed: workcenter sin equipos vinculados bloquea
          button_start salvo que se marque amunet_no_equipment_required (ISO
          13485 requiere justificacion documentada). Validacion adicional de
          que cada equipo este en state='active' (no maintenance ni out_of_service).
          Log automatico en el chatter de la WO cuando se aplica la excepcion.
    """,
    'author': "Amunet",
    'category': 'Manufacturing',
    'version': '19.0.1.2.0',
    'depends': ['mrp', 'stock', 'amunet_quality', 'amunet_equipment_calibration'],
    'data': [
        'data/production_data.xml',
        'security/ir.model.access.csv',
        'wizard/amunet_analysis_wizard_views.xml',
        'reports/production_label_report.xml',
        'views/mrp_production_views.xml',
        'views/mrp_workcenter_views.xml',
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
