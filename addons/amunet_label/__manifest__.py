{
    'name': 'Amunet - Etiquetas',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Generador de etiquetas regulatorias de caja (Cofepris/ISO 13485)',
    'description': """
Amunet - Etiquetas
==================

Modulo independiente para generar etiquetas regulatorias de empaque
secundario (caja del producto). Cumple con los requerimientos
Cofepris / ISO 13485:

- Nombre comercial del producto
- REF (codigo de catalogo)
- LOT (numero de lote)
- Fecha de caducidad
- Lista de contenido de la caja

Flujo
-----
1. En el catalogo de Productos, capturar la lista "Contiene de la caja"
   por SKU (lo que va listado en cada etiqueta).
2. Abrir la app "Etiquetas" -> "Generar etiquetas de caja".
3. Elegir producto, capturar lote y caducidad, indicar cantidad.
4. Imprimir -> PDF tamaño Tabloid 11x17" con 18 etiquetas por hoja
   (grid 3x6, 90x70 mm cada una).

Después podra incorporarse al flujo de Manufactura (orden de
fabricacion) para que el lote y la cantidad se tomen automaticamente.
""",
    'author': 'Amunet S.A. de C.V.',
    'website': 'https://www.amunet.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'product',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/paperformat_data.xml',
        'data/report_data.xml',
        'reports/label_caja_report.xml',
        'views/product_template_views.xml',
        'views/label_print_wizard_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
