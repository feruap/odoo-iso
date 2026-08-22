usuario_karla = env['res.users'].search([('login', '=', 'almacen.mp@amunet.com.mx')], limit=1)
producto = env['product.product'].search([('default_code', '=', 'COCOF01')], limit=1)

# Crear como Karla para que ella sea la solicitante
env_karla = env(user=usuario_karla.id)
solicitud = env_karla['amunet.material.request'].create({
    'line_ids': [(0, 0, {
        'product_id': producto.id,
        'qty_requested': 3.0,
    })],
})
print(f"Solicitud creada: {solicitud.name} | estado={solicitud.state}")

# Avanzar al estado pending_reception usando SQL directo (bypass de flujo para prueba)
env.cr.execute("""
    UPDATE amunet_material_request SET state='pending_reception' WHERE id=%s
""", [solicitud.id])
env.cr.execute("""
    UPDATE amunet_material_request_line 
    SET state='pending_reception', qty_supplied=3, qty_received=0
    WHERE request_id=%s
""", [solicitud.id])
env.cr.commit()
solicitud.invalidate_recordset()
print(f"Estado actualizado: {solicitud.state}")
print(f"URL: https://stagingfc.amunet.com.mx/odoo/material-requests/{solicitud.id}")
