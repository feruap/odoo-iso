# -*- coding: utf-8 -*-
{
    'name': 'Amunet Proveedores — Lista maestra y reevaluación',
    'version': '19.0.1.0.0',
    'summary': 'Lista maestra de proveedores con estatus de calificación y alerta de reevaluación',
    'description': """
Complementa la auditoría de proveedores (amunet_quality) con:
- Lista maestra de proveedores con su estatus de calificación (aprobado/condicional/rechazado),
  última auditoría y próxima auditoría.
- Marca de reevaluación vencida y cron que avisa cuando un proveedor requiere reevaluación.
No reemplaza el motor de calidad; solo agrega la vista maestra y el seguimiento periódico.
""",
    'author': 'Amunet',
    'category': 'Manufacturing/Quality',
    'license': 'LGPL-3',
    'depends': ['mail', 'contacts', 'amunet_quality'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'data/ir_sequence_auditoria.xml',
        'views/res_partner_master_views.xml',
        'views/amunet_auditoria_views.xml',
        'reports/report_auditoria_proveedor.xml',
    ],
    'application': True,
    'installable': True,
}
