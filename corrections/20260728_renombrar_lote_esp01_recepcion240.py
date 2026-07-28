"""
Renombra lote genérico '0000001' de STESP01 en AMP/IN/00240 a ESP01072603.
La recepción está en estado 'assigned' (no validada), el cambio es seguro.

Autorizado por: Karla Fernanda Palma Ramos (almacen.mp@amunet.com.mx)
Fecha: 2026-07-28
"""
lote = env['stock.lot'].browse(1986)
print(f"Lote actual : {lote.name} | producto: {lote.product_id.default_code}")

# Verificar que no exista ya ESP01072603
existe = env['stock.lot'].search([
    ('name', '=', 'ESP01072603'),
    ('product_id', '=', lote.product_id.id)], limit=1)
if existe:
    print("⚠️  ESP01072603 ya existe, no se renombra")
else:
    lote.sudo().write({'name': 'ESP01072603'})
    env.cr.commit()
    print(f"✅ Renombrado: 0000001 → ESP01072603")
