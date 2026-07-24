# Alta DMDMD01 (Dimero D) en linea corta: BoM correcto + ruta 8 pasos + secuencia
# folio /DMD + presentaciones 5 y 20. Datos dictados por Fernando (chatter 2026-07-21).
# Autorizado por Fernando 2026-07-21.
def P(code): return env['product.product'].search([('default_code', '=', code)], limit=1)
def WC(code): return env['mrp.workcenter'].search([('code', '=', code)], limit=1).id
tmpl = env['product.template'].search([('default_code', '=', 'DMDMD01')], limit=1)
bom = env['mrp.bom'].search([('product_tmpl_id', '=', tmpl.id)], limit=1)
assert bom, 'no hay BoM de DMDMD01'
bom.write({'product_qty': 1.0})
bom.bom_line_ids.unlink()
for code, qty in [('SPHMC39', 0.40), ('MPCAR39', 1.0), ('STDSC01', 1.0), ('MPBOL01', 1.0), ('STGOT04', 1.0)]:
    p = P(code)
    env['mrp.bom.line'].create({'bom_id': bom.id, 'product_id': p.id, 'product_qty': qty, 'product_uom_id': p.uom_id.id})
bom.operation_ids.unlink()
ops = [(5, 'Surtido de materiales - DIMERO D', 'AMP', False, False),
       (10, 'Serigrafiado de empaque primario - DIMERO D', 'AC2', True, True),
       (20, 'Corte de hojas maestras compradas - DIMERO D', 'LSC', True, False),
       (30, 'Encartuchado de tiras - DIMERO D', 'ENC', True, True),
       (50, 'Acondicionado 1 - DIMERO D', 'AC1', True, False),
       (55, 'Sellado de Empaque primario - DIMERO D', 'AC1', True, False),
       (60, 'Acondicionado 2 - DIMERO D', 'AC2', True, False),
       (70, 'Resguardo de producto en espera de analisis - DIMERO D', 'PTT', True, False)]
for seq, name, wc, sup, insp in ops:
    env['mrp.routing.workcenter'].create({'bom_id': bom.id, 'sequence': seq, 'name': name,
        'workcenter_id': WC(wc), 'time_cycle_manual': 1,
        'amunet_requires_supervision': sup, 'amunet_requires_inspection': insp})
seq = env['ir.sequence'].search([('prefix', '=', '%(month)s%(y)s/'), ('suffix', '=', '/DMD')], limit=1)
if not seq:
    seq = env['ir.sequence'].create({'name': 'Folio MO DIMERO D (DMD)', 'prefix': '%(month)s%(y)s/',
        'suffix': '/DMD', 'padding': 2, 'number_next': 1, 'implementation': 'standard', 'company_id': env.company.id})
tmpl.mo_sequence_id = seq.id
for qty in [5, 20]:
    if env['amunet.packaging.presentation'].search([('product_tmpl_id', '=', tmpl.id), ('package_qty', '=', qty)], limit=1):
        continue
    pres = env['amunet.packaging.presentation'].create({'product_tmpl_id': tmpl.id, 'package_qty': qty,
        'is_authorized': True, 'authorization_source': 'manual', 'name': 'Caja con %d pruebas' % qty})
    for ccode in ['MICAJ01', 'STBAC01', 'MIMAN01']:
        env['amunet.packaging.presentation.component'].create({'presentation_id': pres.id, 'product_id': P(ccode).id, 'qty_per_box': 1})
env.cr.commit()
print('Receta:', ['%s=%s%s' % (l.product_id.default_code, l.product_qty, l.product_uom_id.name) for l in bom.bom_line_ids])
print('Operaciones:', len(bom.operation_ids))
print('Secuencia:', tmpl.mo_sequence_id.prefix + tmpl.mo_sequence_id.suffix, '| next', seq.number_next)
print('Presentaciones:', [(p.package_qty, [c.product_id.default_code for c in p.component_ids]) for p in env['amunet.packaging.presentation'].search([('product_tmpl_id', '=', tmpl.id)]).sorted('package_qty')])
print('DIMERO PROD OK')
