# -*- coding: utf-8 -*-
# A) Crea el punto de calidad (recepcion) para 4 productos nuevos, clonando el
#    de su mismo tipo (hoja maestra / cartucho). B) Genera la orden de analisis
#    para los 4 lotes que ya estan en cuarentena. Idempotente.
QP = env['amunet.quality.point']
Check = env['amunet.quality.check']

tmpl_hoja = QP.search([('name', 'ilike', 'Hoja Maestra Zika')], limit=1)
tmpl_car = QP.search([('name', 'ilike', 'Cartucho Covid Ag')], limit=1)
print("Plantilla hoja:", tmpl_hoja.name or 'NO ENCONTRADA',
      "| Plantilla cartucho:", tmpl_car.name or 'NO ENCONTRADA')

# (code, nombre del punto = nombre producto, plantilla)
SPECS = [
    ('SPHMC78', 'Hoja Maestra HPV E7', tmpl_hoja),
    ('SPHMC79', 'Hoja Maestra CARBA 5 en 1', tmpl_hoja),
    ('CAR78', 'Cartucho HPV E7', tmpl_car),
    ('CAR79', 'Cartucho CARBA 5 en 1', tmpl_car),
]

print("=== A) PUNTOS DE CALIDAD ===")
for code, name, tmpl in SPECS:
    prod = env['product.product'].search([('default_code', '=', code)], limit=1)
    if not prod:
        print("  producto no encontrado:", code); continue
    if not tmpl:
        print("  sin plantilla para", code); continue
    ya = QP.search([('product_ids', 'in', prod.ids),
                    ('picking_type_ids', 'in', tmpl.picking_type_ids.ids)], limit=1)
    if ya:
        print("  ya existe punto para %s: %s" % (code, ya.name)); continue
    nuevo = tmpl.copy({'name': name, 'product_ids': [(6, 0, [prod.id])]})
    print("  punto creado: [%s] %s (id %s)" % (code, nuevo.name, nuevo.id))

print("=== B) ORDENES DE ANALISIS PARA LOTES EN CUARENTENA ===")
LOTES = ['HMC78072601', 'HMC79072601', 'CAR78072601', 'CAR79072601']
for lot_name in LOTES:
    lot = env['stock.lot'].search([('name', '=', lot_name)], limit=1)
    if not lot:
        print("  lote no existe (ok si es staging):", lot_name); continue
    if Check.search_count([('lot_id', '=', lot.id)]):
        print("  ya tiene QC:", lot_name); continue
    prod = lot.product_id
    ml = env['stock.move.line'].search(
        [('lot_id', '=', lot.id), ('picking_id.picking_type_id.code', '=', 'incoming')],
        order='id desc', limit=1)
    vals = {'product_id': prod.id, 'lot_id': lot.id,
            'sampling_uom_id': prod.uom_id.id}
    if ml and ml.picking_id:
        vals['picking_id'] = ml.picking_id.id
        if ml.picking_id.partner_id:
            vals['partner_id'] = ml.picking_id.partner_id.id
    qc = Check.create(vals)
    print("  QC creado: %s para %s (%s)" % (qc.name, lot_name, prod.default_code))

env.cr.commit()
