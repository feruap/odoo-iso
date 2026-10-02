# Al retirar de produccion el codigo sin commitear de amunet_compras_general,
# sus DOS vistas quedaron en la base pidiendo campos que ya no existen
# (amunet_qty_pedida, amunet_precio_unitario). Resultado: al abrir una
# solicitud de compra nueva, la lista de renglones reventaba en el navegador.
# Se desactivan, no se borran: cuando su autor reintegre el codigo por la via
# normal, el -u del modulo las vuelve a dejar como deben estar.
vistas = env['ir.ui.view'].sudo().browse([3246, 3247])
for v in vistas:
    print('%-5s %-38s activa: %s' % (v.id, v.name, v.active))
vistas.write({'active': False})
env.cr.commit()
print()
for v in vistas:
    v.invalidate_recordset()
    print('%-5s %-38s ahora: %s' % (v.id, v.name, v.active))

print()
print('=== quedan vistas activas pidiendo esos campos? ===')
restan = env['ir.ui.view'].sudo().search([
    ('active', '=', True),
    '|', ('arch_db', 'like', 'amunet_qty_pedida'),
         ('arch_db', 'like', 'amunet_precio_unitario')])
print('  ', restan.mapped('name') or 'ninguna')
