# Alta ROTADENET (DMRAV01) en linea corta: crea BoM (1 por pieza, CON el vial
# de corrimiento STBPR03 -pruebas HECES- como material de fabricacion; la imagen
# decia STBPR04 pero el correcto es STBPR03 por Fernando), ruta 8 pasos, secuencia
# folio /RA, presentaciones 5 y 20 (Caja + Instructivo, sin vial). Nombre ->
# "ROTADENET". Datos dictados por Fernando (canal 50, 2026-07-22).
def P(code):
    return env['product.product'].search([('default_code', '=', code)], limit=1)
def WC(code):
    return env['mrp.workcenter'].search([('code', '=', code)], limit=1).id

tmpl = env['product.template'].search([('default_code', '=', 'DMRAV01')], limit=1)
assert tmpl, 'no existe DMRAV01'

# 0) Nombre -> ROTADENET (ambos idiomas)
tmpl.with_context(lang='en_US').write({'name': 'ROTADENET'})
tmpl.with_context(lang='es_MX').write({'name': 'ROTADENET'})

# 1) BoM (crear si no existe): 1 por pieza; el vial STBPR04 SI va en el BoM
bom = env['mrp.bom'].search([('product_tmpl_id', '=', tmpl.id)], limit=1)
if not bom:
    bom = env['mrp.bom'].create({'product_tmpl_id': tmpl.id, 'product_qty': 1.0,
                                 'type': 'normal', 'product_uom_id': tmpl.uom_id.id})
    print('BoM creado id', bom.id)
else:
    bom.write({'product_qty': 1.0})
bom.bom_line_ids.unlink()
for code, qty in [('SPHMC27', 0.40), ('MPCAR27', 1.0), ('STGOT05', 1.0),
                  ('STDSC01', 1.0), ('STBPR03', 1.0), ('MPBOL01', 1.0)]:
    p = P(code)
    assert p, 'falta componente ' + code
    env['mrp.bom.line'].create({'bom_id': bom.id, 'product_id': p.id,
                                'product_qty': qty, 'product_uom_id': p.uom_id.id})

# 2) Ruta 8 pasos (linea corta), 1 min c/u
bom.operation_ids.unlink()
ops = [(5,  'Surtido de materiales - ROTADENET',                    'AMP', False, False),
       (10, 'Serigrafiado de empaque primario - ROTADENET',        'AC2', True,  True),
       (20, 'Corte de hojas maestras compradas - ROTADENET',       'LSC', True,  False),
       (30, 'Encartuchado de tiras - ROTADENET',                   'ENC', True,  True),
       (50, 'Acondicionado 1 - ROTADENET',                         'AC1', True,  False),
       (55, 'Sellado de Empaque primario - ROTADENET',             'AC1', True,  False),
       (60, 'Acondicionado 2 - ROTADENET',                         'AC2', True,  False),
       (70, 'Resguardo de producto en espera de analisis - ROTADENET', 'PTT', True, False)]
for seq_, name, wc, sup, insp in ops:
    env['mrp.routing.workcenter'].create({'bom_id': bom.id, 'sequence': seq_, 'name': name,
        'workcenter_id': WC(wc), 'time_cycle_manual': 1,
        'amunet_requires_supervision': sup, 'amunet_requires_inspection': insp})

# 3) Secuencia de folio MO, sufijo /RA
seq = env['ir.sequence'].search([('prefix', '=', '%(month)s%(y)s/'), ('suffix', '=', '/RA')], limit=1)
if not seq:
    seq = env['ir.sequence'].create({'name': 'Folio MO ROTADENET (RA)', 'prefix': '%(month)s%(y)s/',
        'suffix': '/RA', 'padding': 2, 'number_next': 1, 'implementation': 'standard', 'company_id': env.company.id})
tmpl.mo_sequence_id = seq.id

# 4) Presentaciones 5 y 20: Caja + Instructivo (el vial NO va aqui, va en el BoM)
for qty in [5, 20]:
    if env['amunet.packaging.presentation'].search([('product_tmpl_id', '=', tmpl.id), ('package_qty', '=', qty)], limit=1):
        continue
    pres = env['amunet.packaging.presentation'].create({'product_tmpl_id': tmpl.id, 'package_qty': qty,
        'is_authorized': True, 'authorization_source': 'manual', 'name': 'Caja con %d pruebas' % qty})
    for ccode in ['MICAJ01', 'MIMAN01']:
        env['amunet.packaging.presentation.component'].create(
            {'presentation_id': pres.id, 'product_id': P(ccode).id, 'qty_per_box': 1})

env.cr.commit()
print('Nombre:', tmpl.with_context(lang='es_MX').name)
print('Receta:', ['%s=%s%s' % (l.product_id.default_code, l.product_qty, l.product_uom_id.name) for l in bom.bom_line_ids])
print('Operaciones:', len(bom.operation_ids))
print('Secuencia:', tmpl.mo_sequence_id.prefix + tmpl.mo_sequence_id.suffix, '| next', seq.number_next)
print('Presentaciones:', [(p.package_qty, [c.product_id.default_code for c in p.component_ids]) for p in env['amunet.packaging.presentation'].search([('product_tmpl_id', '=', tmpl.id)]).sorted('package_qty')])
print('ROTADENET STAGING OK')
