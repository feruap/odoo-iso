# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Visibilidad de precios restringida',
    'summary': 'Oculta TODOS los precios a todos excepto al grupo "Ver precios" (Fernando).',
    'description': """
ESTRICTO: solo Fernando (miembro del grupo amunet_price_visibility.group_price_viewer)
puede ver precios, costos, totales y montos en CUALQUIER vista, reporte o exportacion.
Los demas usuarios pueden seguir operando (crear PO, recibir, hacer BoM, validar
facturas) pero el campo monetario simplemente no se renderiza para ellos.

Cobertura v19.0.2.0.0:
- product.template / product.product: list_price, standard_price (form, list, easy, pricelist)
- product.supplierinfo: price, discount (form, list, kanban)
- purchase.order: amount_total, amount_untaxed, amount_tax en TODAS las vistas
  (list, kanban, calendar, pivot, graph, activity, form)
- purchase.order.line: price_unit, price_subtotal, price_total, discount, taxes_id
  (tree y form, incluyendo purchase.history)
- purchase.report (analytical): price_total, price_average
- mrp.bom.line / mrp.production: costo del componente
- stock.move (valuation), stock.lot (standard_price)
- account.move (vendor bills): amount_total, amount_untaxed, amount_tax
- account.move.line: price_unit, price_subtotal, price_total, debit, credit cuando
  pertenecen a una vendor bill
- PDF: report_purchaseorder_document, report_purchasequotation_document,
  report_invoice_document (al menos para vendor bills)
- Menus: Compras > Reportes (purchase.report) restringido al grupo

Si alguien no tiene el grupo, el campo NO existe en su contexto y por tanto NO se
puede mostrar, exportar ni filtrar.
    """,
    'author': 'Amunet',
    'category': 'Hidden',
    'version': '19.0.3.1.0',
    'depends': [
        'product',
        'purchase',
        'stock',
        'stock_account',
        'mrp',
        'account',
    ],
    'data': [
        'security/security.xml',
        'data/price_viewer_user.xml',
        'views/product_views.xml',
        'views/supplierinfo_views.xml',
        'views/purchase_views.xml',
        'views/purchase_extended_views.xml',
        'views/product_extended_views.xml',
        'views/stock_views.xml',
        'views/mrp_views.xml',
        'views/account_views.xml',
        'views/menu_security.xml',
        'reports/purchase_report_qweb.xml',
        'reports/invoice_report_qweb.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
