{
    'name': 'Amunet - Programa de Auditorías (ISO 13485 §8.2.4 / §7.4)',
    'version': '19.0.1.0.0',
    'category': 'Quality',
    'summary': 'Auditorías internas y a proveedores con checklists y generación automática de CAPAs',
    'description': """
Gestión del Programa de Auditorías para Calidad bajo ISO 13485.

Funcionalidades:

- Auditorías internas (a departamentos) y externas (a proveedores)
- Checklists dinámicos por cláusula de norma
- Registro y clasificación de Hallazgos / No Conformidades
- Botón "Crear CAPA" que genera automáticamente una Acción Correctiva
  en amunet_quality con trazabilidad completa (proveedor, hallazgo, auditoría)
- Actualización automática del estatus de calidad del proveedor
- Registro en Audit Log (21 CFR Part 11) de cada CAPA generada
    """,
    'author': 'DIC Consultores - Rafael López Flores',
    'website': 'https://www.amunet.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'amunet_quality',
        'hr',
        'purchase',
        'mail',
    ],
    'data': [
        # Seguridad
        'security/amunet_auditorias_security.xml',
        'security/ir.model.access.csv',

        # Datos maestros
        'data/ir_sequence_data.xml',

        # Vistas
        'views/amunet_auditoria_views.xml',
        'views/amunet_quality_capa_ext_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
