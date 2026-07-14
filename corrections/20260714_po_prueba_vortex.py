env = env(su=True)

producto = env['product.product'].browse(446)  # EQVOR01 Vortex
proveedor = env['res.partner'].browse(526)      # ZZ PRUEBA N3000

po = env['purchase.order'].create({
    'partner_id': proveedor.id,
    'origin': '⚠️ PRUEBA — NO ES ORDEN REAL — TEST FLUJO RECEPCION/CALIDAD',
    'note': 'ORDEN DE PRUEBA creada para validar el flujo de recepción con separación de equipos buenos/malos. NO procesar en producción.',
    'order_line': [(0, 0, {
        'product_id': producto.id,
        'product_qty': 5,
        'price_unit': 1,
        'name': '[PRUEBA] Vortex — 5 unidades para test de flujo',
        'date_planned': '2026-07-14 12:00:00',
    })],
})
print("PO creada:", po.name, '| Estado:', po.state)
print("Origen:", po.origin)

po.button_confirm()
print("PO confirmada:", po.name, '| Estado:', po.state)

recepcion = po.picking_ids[0]
print("Recepción generada:", recepcion.name, '| Estado:', recepcion.state)
print("URL staging: https://stagingfc.amunet.com.mx/odoo/inventory/receipts/" + str(recepcion.id))

env.cr.commit()
