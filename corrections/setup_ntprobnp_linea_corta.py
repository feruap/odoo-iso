# Alta NT-proBNP (DMPRO01) en linea corta: corrige BoM (1 por pieza) + ruta 8
# pasos + secuencia folio /ICN + presentaciones 2/5/10 (vial STBPR01 solo en 5 y 10).
# Datos dictados por Fernando (chatter canal 50, 2026-07-22). El nombre del
# producto lo ajusta Fernando aparte. Autorizado por Fernando 2026-07-22.
def P(code):
    return env['product.product'].search([('default_code', '=', code)], limit=1)
def WC(code):
    return env['mrp.workcenter'].search([('code', '=', code)], limit=1).id

tmpl = env['product.template'].search([('default_code', '=', 'DMPRO01')], limit=1)
assert tmpl, 'no existe DMPRO01'
bom = env['mrp.bom'].search([('product_tmpl_id', '=', tmpl.id)], limit=1)
assert bom, 'no hay BoM de DMPRO01'

# 1) BoM: 1 por pieza, componentes correctos (SIN el vial, que es acondicionado)
bom.write({'product_qty': 1.0})
bom.bom_line_ids.unlink()
for code, qty in [('SPHMC59', 0.40), ('MPCAR59', 1.0), ('STDSC01', 1.0), ('MPBOL01', 1.0), ('STGOT04', 1.0)]:
    p = P(code)
    assert p, 'falta componente ' + code
    env['mrp.bom.line'].create({'bom_id': bom.id, 'product_id': p.id,
                                'product_qty': qty, 'product_uom_id': p.uom_id.id})

# 2) Ruta 8 pasos (igual linea corta), tiempo 1 min c/u
bom.operation_ids.unlink()
ops = [(5,  'Surtido de materiales - NT-proBNP',                    'AMP', False, False),
       (10, 'Serigrafiado de empaque primario - NT-proBNP',        'AC2', True,  True),
       (20, 'Corte de hojas maestras compradas - NT-proBNP',       'LSC', True,  False),
       (30, 'Encartuchado de tiras - NT-proBNP',                   'ENC', True,  True),
       (50, 'Acondicionado 1 - NT-proBNP',                         'AC1', True,  False),
       (55, 'Sellado de Empaque primario - NT-proBNP',             'AC1', True,  False),
       (60, 'Acondicionado 2 - NT-proBNP',                         'AC2', True,  False),
       (70, 'Resguardo de producto en espera de analisis - NT-proBNP', 'PTT', True, False)]
for seq_, name, wc, sup, insp in ops:
    env['mrp.routing.workcenter'].create({'bom_id': bom.id, 'sequence': seq_, 'name': name,
        'workcenter_id': WC(wc), 'time_cycle_manual': 1,
        'amunet_requires_supervision': sup, 'amunet_requires_inspection': insp})

# 3) Secuencia de folio MO, sufijo /ICN
seq = env['ir.sequence'].search([('prefix', '=', '%(month)s%(y)s/'), ('suffix', '=', '/ICN')], limit=1)
if not seq:
    seq = env['ir.sequence'].create({'name': 'Folio MO NT-proBNP (ICN)', 'prefix': '%(month)s%(y)s/',
        'suffix': '/ICN', 'padding': 2, 'number_next': 1, 'implementation': 'standard', 'company_id': env.company.id})
tmpl.mo_sequence_id = seq.id

# 4) Presentaciones 2/5/10: caja+instructivo siempre; vial STBPR01 solo en 5 y 10
pres_spec = {2: ['MICAJ01', 'MIMAN01'],
             5: ['MICAJ01', 'STBPR01', 'MIMAN01'],
             10: ['MICAJ01', 'STBPR01', 'MIMAN01']}
for qty in sorted(pres_spec):
    if env['amunet.packaging.presentation'].search([('product_tmpl_id', '=', tmpl.id), ('package_qty', '=', qty)], limit=1):
        continue
    pres = env['amunet.packaging.presentation'].create({'product_tmpl_id': tmpl.id, 'package_qty': qty,
        'is_authorized': True, 'authorization_source': 'manual', 'name': 'Caja con %d pruebas' % qty})
    for ccode in pres_spec[qty]:
        env['amunet.packaging.presentation.component'].create(
            {'presentation_id': pres.id, 'product_id': P(ccode).id, 'qty_per_box': 1})

env.cr.commit()
print('Receta:', ['%s=%s%s' % (l.product_id.default_code, l.product_qty, l.product_uom_id.name) for l in bom.bom_line_ids])
print('Operaciones:', len(bom.operation_ids))
print('Secuencia:', tmpl.mo_sequence_id.prefix + tmpl.mo_sequence_id.suffix, '| next', seq.number_next)
print('Presentaciones:', [(p.package_qty, [c.product_id.default_code for c in p.component_ids]) for p in env['amunet.packaging.presentation'].search([('product_tmpl_id', '=', tmpl.id)]).sorted('package_qty')])
print('NT-proBNP STAGING OK')
