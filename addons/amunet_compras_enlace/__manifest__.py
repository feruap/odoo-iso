{
    'name': 'Amunet - Enlace de compras y aviso de recepciones',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Purchase',
    'summary': 'Genera ordenes de compra desde Solicitudes de Material y avisa a almacen las recepciones del dia',
    'description': """
Enlace de compras Amunet
========================

Cierra el hueco entre el marketplace interno y el modulo de compras.

1. Accion "Generar orden de compra" en la Solicitud de Material.
   - Compra unicamente el faltante (pedido - surtido - existencia).
   - Deduce el proveedor del supplierinfo, o de la liga de marketplace
     (Amazon / Mercado Libre).
   - Deja el precio en cero: los precios los captura solo Direccion, tal como
     lo impone amunet_price_visibility.

2. Aviso diario 8:30 am a los buzones de almacen con las recepciones
   esperadas del dia, las atrasadas y las solicitudes pendientes.
""",
    'author': 'Amunet S.A. de C.V.',
    'website': 'https://www.amunet.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'purchase_stock',
        'amunet_material_request',
        'amunet_marketplace',
    ],
    'data': [
        'data/ir_actions_server.xml',
        'data/ir_cron.xml',
    ],
    'installable': True,
    'application': False,
}
