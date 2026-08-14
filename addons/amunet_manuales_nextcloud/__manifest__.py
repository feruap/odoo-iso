{
    'name': 'Amunet - Manuales a Nextcloud',
    'version': '19.0.1.0.0',
    'category': 'Amunet',
    'summary': 'Sube el PDF de un manual aprobado a Nextcloud automaticamente',
    'description': (
        'Al cambiar el estado de un documento de tipo Manual a Vigente, '
        'sube el archivo adjunto a la carpeta de Nextcloud configurada en '
        'los parametros del sistema (nextcloud.manuales.*).'
    ),
    'depends': ['amunet_documentos'],
    'data': [],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
