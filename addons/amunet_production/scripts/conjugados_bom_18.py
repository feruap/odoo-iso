# BoM de los 18 conjugados restantes con datos (Flu A / SPCDE01 ya tiene el 146).
# Reglas Mery 17-sep-2026: 1 mL NPS -> 100 uL de conjugado a D.O. 10;
# SAB y bloqueo 1:1 con NPS; diluyente = volumen final.
ML = env['uom.uom'].browse(11)
INS = {  # clave -> product_id
    'SPNPS01': 578, 'SPSPC04': 592, 'SPSPC05': 593,
    'SPSPB01': 588, 'SPSPB02': 589, 'SPSPB03': 581,
    'SPSDC01': 586, 'SPSDC02': 584,
}
# clave, nps_mL, pH, bloqueo(CAS/BSA/CB), diluyente(AD0/AD1)
DATOS = [
    ('SPCDE21', 5, '8.5', 'CB',  'AD0'),
    ('SPCDE08', 5, '7.5', 'CAS', 'AD1'),
    ('SPCDE17', 5, '8.5', 'CAS', 'AD1'),
    ('SPCDE02', 5, '8.5', 'CAS', 'AD0'),
    ('SPCDE12', 5, '8.5', 'CAS', 'AD0'),
    ('SPCDE14', 5, '7.5', 'CAS', 'AD1'),
    ('SPCDE19', 5, '7.5', 'BSA', 'AD0'),
    ('SPCDE22', 5, '7.5', 'BSA', 'AD0'),
    ('SPCDE29', 5, '8.5', 'BSA', 'AD0'),
    ('SPCDE09', 5, '7.5', 'CAS', 'AD1'),
    ('SPCDE10', 5, '7.5', 'CAS', 'AD1'),
    ('SPCDE03', 3, '8.5', 'CAS', 'AD1'),
    ('SPCDE18', 5, '7.5', 'CAS', 'AD1'),
    ('SPCDE24', 5, '7.5', 'CAS', 'AD1'),
    ('SPCDE26', 5, '7.5', 'CAS', 'AD1'),
    ('SPCDE13', 5, '7.5', 'CAS', 'AD1'),
    ('SPCDE20', 5, '7.5', 'CAS', 'AD1'),
    ('SPCDE23', 5, '7.5', 'CAS', 'AD1'),
]
SAB = {'7.5': 'SPSPC04', '8.5': 'SPSPC05'}
DIL = {'AD0': 'SPSDC01', 'AD1': 'SPSDC02'}
P = env['product.product']
Bom = env['mrp.bom']
creados = []
for clave, nps, ph, bloq, dil in DATOS:
    prod = P.search([('default_code', '=', clave)], limit=1)
    if not prod:
        print('%s NO existe' % clave); continue
    if Bom.search([('product_tmpl_id', '=', prod.product_tmpl_id.id), ('active', '=', True)]):
        print('%s ya tiene BoM' % clave); continue
    rinde = round(nps * 0.1, 4)          # 100 uL por mL de NPS
    lineas = [
        (0, 0, {'product_id': INS['SPNPS01'], 'product_qty': float(nps), 'product_uom_id': ML.id}),
        (0, 0, {'product_id': INS[SAB[ph]],  'product_qty': float(nps), 'product_uom_id': ML.id}),
    ]
    if bloq == 'CAS':
        lineas.append((0, 0, {'product_id': INS['SPSPB03'], 'product_qty': float(nps), 'product_uom_id': ML.id}))
    elif bloq == 'BSA':
        lineas.append((0, 0, {'product_id': INS['SPSPB01' if ph == '7.5' else 'SPSPB02'],
                              'product_qty': float(nps), 'product_uom_id': ML.id}))
    else:  # Caseina y BSA (control de raton): mitad y mitad
        lineas.append((0, 0, {'product_id': INS['SPSPB03'], 'product_qty': nps / 2.0, 'product_uom_id': ML.id}))
        lineas.append((0, 0, {'product_id': INS['SPSPB01' if ph == '7.5' else 'SPSPB02'],
                              'product_qty': nps / 2.0, 'product_uom_id': ML.id}))
    lineas.append((0, 0, {'product_id': INS[DIL[dil]], 'product_qty': rinde, 'product_uom_id': ML.id}))
    bom = Bom.create({
        'product_tmpl_id': prod.product_tmpl_id.id,
        'product_qty': rinde, 'product_uom_id': ML.id,
        'type': 'normal', 'company_id': env.company.id,
        'bom_line_ids': lineas,
    })
    creados.append((clave, bom.id, rinde, len(bom.bom_line_ids)))
    print('%-9s BoM %-4s rinde %.2f mL  | %s lineas (NPS %s mL, pH %s, %s, %s)' % (
        clave, bom.id, rinde, len(bom.bom_line_ids), nps, ph, bloq, dil))
env.cr.commit()
print('COMMIT OK - %s BoM creados' % len(creados))
