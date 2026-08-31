{
    'name': 'Amunet - Revision de mapeo Woo',
    'version': '19.0.1.0.0',
    'summary': 'Revision diaria del mapeo Woo<->Odoo y decision de clave unica',
    'description': """
Complemento de solo lectura sobre amunet_woocommerce.

1) Revision automatica diaria (23:00) que compara el catalogo de la tienda
   contra el mapeo y REPORTA: productos publicados sin emparejar, mapeos
   huerfanos (ya no existen en la tienda) y cambios (SKU / nombre / estado).
   NO escribe nada en WooCommerce. Solo lee (GET) y registra el resultado
   en Odoo.

2) Columnas para que Almacen decida que clave es la buena (la de la pagina
   o la de Odoo), dejando registro de quien decidio y cuando.

Nota de diseno: el modulo amunet_woocommerce es de solo lectura por contrato
y sus pruebas prohiben crear cron sobre modelos amunet.woo.*. Por eso esta
revision vive en un modelo aparte (amunet.revision.mapeo) y tampoco escribe
en la tienda: se respeta el contrato original.
""",
    'author': 'Amunet',
    'license': 'LGPL-3',
    'category': 'Inventory',
    'depends': ['amunet_woocommerce'],
    'data': [
        'security/ir.model.access.csv',
        'views/revision_mapeo_views.xml',
        'views/woo_product_mapping_views.xml',
        'data/ir_cron.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
