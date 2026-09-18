Tmpl = env['product.template']
if Tmpl.search([('default_code', '=', 'SPCDE29')], limit=1):
    print('SPCDE29 ya existe')
else:
    base = Tmpl.search([('default_code', '=', 'SPCDE22')], limit=1)  # Sifilis
    nombre = 'Solución de conjugado control Sífilis'
    vals = {
        'default_code': 'SPCDE29',
        'name': nombre,
        'type': base.type,
        'is_storable': True,
        'categ_id': base.categ_id.id,
        'uom_id': base.uom_id.id,
        'tracking': 'lot',
        'purchase_ok': False,
        'sale_ok': False,
        'amunet_expiration_text': base.amunet_expiration_text,
        'route_ids': [(6, 0, [15])],
    }
    t = Tmpl.with_context(amunet_alta_autorizada=True).create(vals)
    t.with_context(lang='es_MX', amunet_alta_autorizada=True).write({'name': nombre})
    print('SPCDE29 creado id=%s | %s | categ=%s | uom=%s | caducidad=%s' % (
        t.id, t.name, t.categ_id.complete_name, t.uom_id.name, t.amunet_expiration_text))
env.cr.commit()
print('COMMIT OK')
