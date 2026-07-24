# Migracion de DATOS del entorno de soluciones a produccion:
# 1) Almacen ARU (Reactivos en uso) + ubicacion ARU/Desarrollo
# 2) Categorias que enrutan reactivos a ARU (amunet_route_to_aru)
# 3) Producto generico STDES01 "Solucion de desarrollo"
# Autorizado por Fernando 2026-07-21.
Wh = env['stock.warehouse'].sudo()
Loc = env['stock.location'].sudo()

# 1) ARU
aru = Wh.search([('code', '=', 'ARU')], limit=1)
if not aru:
    aru = Wh.create({'name': 'Almacén de reactivos en uso', 'code': 'ARU',
                     'reception_steps': 'one_step', 'delivery_steps': 'ship_only'})
    print('ARU creado id', aru.id)
else:
    print('ARU ya existia id', aru.id)
# ARU/Desarrollo
dev = Loc.search([('complete_name', '=', 'ARU/Desarrollo')], limit=1)
if not dev:
    dev = Loc.create({'name': 'Desarrollo', 'location_id': aru.view_location_id.id,
                      'usage': 'internal'})
    print('ARU/Desarrollo creado id', dev.id)
else:
    print('ARU/Desarrollo ya existia id', dev.id)

# 2) Categorias a ARU
for cn in ['Materia prima / Agua', 'Materia prima / Reactivo']:
    cat = env['product.category'].search([('complete_name', '=', cn)], limit=1)
    if cat:
        cat.amunet_route_to_aru = True
        print('categoria enrutada a ARU:', cn)
    else:
        print('OJO categoria no encontrada:', cn)

# 3) STDES01
Tmpl = env['product.template']
if not Tmpl.search([('default_code', '=', 'STDES01')], limit=1):
    categ = env['product.category'].search([('complete_name', '=', 'Semiprocesado / Soluciones de trabajo')], limit=1)
    ref = Tmpl.search([('default_code', '=', 'SPLPT01')], limit=1)
    assert categ, 'no existe la categoria de soluciones en prod'
    t = Tmpl.with_context(amunet_alta_autorizada=True).create({
        'name': 'Solución de desarrollo', 'default_code': 'STDES01',
        'categ_id': categ.id, 'type': ref.type if ref else 'consu', 'is_storable': True,
        'tracking': 'lot', 'use_expiration_date': True,
        'amunet_es_desarrollo': True, 'amunet_req_quality_control': False,
        'uom_id': ref.uom_id.id if ref else False})
    print('STDES01 creado id', t.id, '| es_desarrollo', t.amunet_es_desarrollo)
else:
    print('STDES01 ya existia')
env.cr.commit()
print('MIGRACION DATOS OK')
