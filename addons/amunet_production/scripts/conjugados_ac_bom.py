# Anticuerpo/antigeno en las recetas de conjugado, en CANTIDAD (masa), no volumen.
# cantidad = concentracion objetivo (ug/mL) x volumen de nanoparticulas (mL)
# Los anticuerpos se manejan en mg; se crea la unidad ug para que la receta se
# lea en numeros de laboratorio (37.5 ug) y no en 0.0375 mg.
Uom = env['uom.uom']
ug = Uom.search([('name', '=', 'µg')], limit=1)
if not ug:
    mg = Uom.browse(42)
    ug = Uom.create({'name': 'µg', 'relative_factor': 0.001, 'relative_uom_id': mg.id})
    print('Unidad µg creada (id %s, 1 µg = 0.001 mg)' % ug.id)
else:
    print('Unidad µg ya existe (id %s)' % ug.id)

# conjugado -> (clave del anticuerpo, ug/mL, mL de NPS)
DATOS = {
    'SPCDE01': ('MPANT31', 7.5, 5), 'SPCDE02': ('MPANT30', 5.0, 5),
    'SPCDE03': ('MPANT34', 7.5, 3), 'SPCDE08': ('MPANT05', 8.0, 5),
    'SPCDE09': ('MPAG08', 10.0, 5), 'SPCDE10': ('MPANT32', 10.0, 5),
    'SPCDE12': ('MPANT10', 10.0, 5), 'SPCDE13': ('MPANT13', 15.0, 5),
    'SPCDE14': ('MPANT36', 15.0, 5), 'SPCDE17': ('MPANT38', 10.0, 5),
    'SPCDE18': ('MPANT16', 10.0, 5), 'SPCDE19': ('MPANT56', 15.0, 5),
    'SPCDE20': ('MPANT67', 5.0, 5), 'SPCDE21': ('MPANT06', 10.0, 5),
    'SPCDE22': ('MPAG10', 10.0, 5), 'SPCDE23': ('MPANT54', 5.0, 5),
    'SPCDE24': ('MPANT50', 5.0, 5), 'SPCDE26': ('MPANT40', 15.0, 5),
    'SPCDE29': ('MPANT48', 10.0, 5),
}
P = env['product.product']; Bom = env['mrp.bom']
faltan = []
for conj, (ac, conc, nps) in sorted(DATOS.items()):
    prod = P.search([('default_code', '=', conj)], limit=1)
    bom = Bom.search([('product_tmpl_id', '=', prod.product_tmpl_id.id), ('active', '=', True)], limit=1)
    acp = P.search([('default_code', '=', ac)], limit=1)
    if not acp:
        faltan.append((conj, ac)); print('%-9s FALTA el producto %s en staging' % (conj, ac)); continue
    if bom.bom_line_ids.filtered(lambda l: l.product_id == acp):
        print('%-9s ya tiene %s' % (conj, ac)); continue
    cant = conc * nps
    env['mrp.bom.line'].create({
        'bom_id': bom.id, 'product_id': acp.id,
        'product_qty': cant, 'product_uom_id': ug.id,
    })
    print('%-9s + %-8s %6.1f µg  (%s µg/mL x %s mL)' % (conj, ac, cant, conc, nps))
env.cr.commit()
print('COMMIT OK' + (' | faltantes: %s' % faltan if faltan else ''))
