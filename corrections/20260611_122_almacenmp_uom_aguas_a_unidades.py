# Cambiar unidad de medida de aguas destiladas: Litros -> Unidades
# Solicitud de Karla (almacen.mp) — los envases se cuentan por pieza, no por volumen
uom_units = env['uom.uom'].search([('name', '=', 'Units')], limit=1)
if not uom_units:
    uom_units = env['uom.uom'].search([('name', '=', 'Unidades')], limit=1)

if not uom_units:
    print("ERROR: No se encontró la UdM 'Units'/'Unidades'")
else:
    productos = env['product.template'].search([
        ('name', 'in', ['Agua destilada', 'Agua bidestilada', 'Agua tridestilada'])
    ])
    print(f"Productos encontrados: {productos.mapped('name')}")
    productos.write({'uom_id': uom_units.id})
    print(f"OK — {len(productos)} productos actualizados a UdM: {uom_units.name}")
