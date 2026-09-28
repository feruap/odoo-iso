{
    'name': 'Amunet - Lista Maestra de Claves',
    'version': '19.0.1.0.0',
    'category': 'Quality',
    'summary': 'Catálogo de claves de productos por clasificación (ISO 13485)',
    'author': 'Amunet',
    'license': 'LGPL-3',
    'depends': ['amunet_documentos'],
    'data': [
        'security/ir.model.access.csv',
        'security/rules.xml',
        'views/clave_views.xml',
        'views/menus.xml',
        'data/seeds_semiprocesado.xml',
        'data/seeds_semiterminado.xml',
        'data/seeds_materiaprima.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'amunet_lista_claves/static/src/css/lista_claves.css',
            'amunet_lista_claves/static/src/js/lista_claves.js',
            'amunet_lista_claves/static/src/xml/lista_claves.xml',
        ],
    },
    'installable': True,
    'application': False,
}
