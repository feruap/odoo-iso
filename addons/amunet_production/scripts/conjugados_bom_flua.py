# BoM PILOTO: Flu A (SPCDE01). Tanda = 1 tubo de 5 mL de nanoparticulas.
# Reglas dadas por Mery 17-sep-2026:
#   1 mL NPS -> 100 uL de conjugado a D.O. 10
#   resuspension y bloqueo proporcionales 1:1 con las NPS
#   diluyente = volumen final (incluye los 30 uL de resuspension del boton)
P = env['product.product']
ML = env['uom.uom'].browse(11)

conj = P.browse(2159)          # SPCDE01
if env['mrp.bom'].search([('product_tmpl_id', '=', conj.product_tmpl_id.id), ('active', '=', True)]):
    print('Ya tiene BoM activo, no se crea otro')
else:
    bom = env['mrp.bom'].create({
        'product_tmpl_id': conj.product_tmpl_id.id,
        'product_qty': 0.5,            # 0.5 mL de conjugado a D.O. 10
        'product_uom_id': ML.id,
        'type': 'normal',
        'company_id': env.company.id,
        'bom_line_ids': [
            (0, 0, {'product_id': 578, 'product_qty': 5.0, 'product_uom_id': ML.id}),   # NPS
            (0, 0, {'product_id': 592, 'product_qty': 5.0, 'product_uom_id': ML.id}),   # Borato pH 7.5
            (0, 0, {'product_id': 581, 'product_qty': 5.0, 'product_uom_id': ML.id}),   # Bloqueo Caseina
            (0, 0, {'product_id': 584, 'product_qty': 0.5, 'product_uom_id': ML.id}),   # Diluyente AD1
        ],
    })
    print('BoM %s creado para %s -> produce %s %s' % (
        bom.id, conj.default_code, bom.product_qty, bom.product_uom_id.name))
    for l in bom.bom_line_ids:
        print('   %-9s %-45s %s %s' % (
            l.product_id.default_code, l.product_id.name[:45], l.product_qty, l.product_uom_id.name))
env.cr.commit()
print('COMMIT OK')
