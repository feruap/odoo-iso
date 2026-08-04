# Ajusta el folio de la orden de TB al mes de inicio real (agosto): 0726 -> 0826
NUEVO = '0826/01/TUB'
mo = env['mrp.production'].browse(88)
print("MO actual:", mo.name, "| estado:", mo.state)
# conflicto?
conf_mo = env['mrp.production'].search([('name','=',NUEVO)])
conf_lot = env['stock.lot'].search([('name','=',NUEVO),('product_id','=',mo.product_id.id)])
if conf_mo or conf_lot:
    print("CONFLICTO: ya existe", NUEVO, "- NO se cambia")
else:
    viejo = mo.name
    mo.sudo().write({'name': NUEVO})
    # lote(s) producido(s) con el folio viejo
    for lot in mo.lot_producing_ids:
        if lot.name == viejo:
            lot.sudo().write({'name': NUEVO})
            print("lote renombrado:", viejo, "->", NUEVO)
    # por si el lote 2017 no está en lot_producing_ids
    l = env['stock.lot'].browse(2017)
    if l.exists() and l.name == viejo:
        l.sudo().write({'name': NUEVO})
        print("lote 2017 renombrado ->", NUEVO)
    print("MO renombrada:", viejo, "->", mo.name)
env.cr.commit()
