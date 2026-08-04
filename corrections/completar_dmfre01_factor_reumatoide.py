# Completa el producto terminado DMFRE01 (FACTOR REUMATOIDE) linea corta. Portable.
#  - Nombre "FACTOR REUMATOIDE" (el de la imagen)
#  - Secuencia de folio MO /FRE
#  - BoM (por pieza): SPHMC42 0.40cm, MPCAR42 1, STDSC01 1, STBPR01 1, STGOT02 1, MPBOL01 1
#    (reemplaza BoM 47: product_qty=70, gotero STGOT01 equivocado)
#    El vial STBPR01 SI va en la receta (asi lo indica la imagen); empaque sin vial.
#    Gotero = STGOT02 (5 ul, capilar chico punta larga).
#  - Ruta 8 pasos estandar
#  - Presentaciones 5 y 20 pzas: MICAJ01 + MIMAN01
# Autorizado por Fernando 2026-07-27.
Prod = env['product.product'].sudo()
t = env['product.template'].sudo().search([('default_code', '=', 'DMFRE01')], limit=1)
assert t, 'DMFRE01 no existe'

def pp(code):
    p = Prod.search([('default_code', '=', code)], limit=1)
    assert p, 'falta producto %s' % code
    return p

def wc(name):
    w = env['mrp.workcenter'].sudo().search([('name', '=', name)], limit=1)
    assert w, 'falta centro %s' % name
    return w.id

t.with_context(lang='en_US').write({'name': 'FACTOR REUMATOIDE'})
t.with_context(lang='es_MX').write({'name': 'FACTOR REUMATOIDE'})
print('Nombre:', t.with_context(lang='es_MX').name)

if not t.mo_sequence_id:
    seq = env['ir.sequence'].sudo().create({
        'name': 'Folio MO FACTOR REUMATOIDE', 'prefix': '%(month)s%(y)s/', 'suffix': '/FRE',
        'padding': 2, 'number_next': 1, 'implementation': 'standard', 'company_id': 1})
    t.mo_sequence_id = seq.id
    print('Secuencia creada:', seq.prefix + '##' + seq.suffix)
else:
    t.mo_sequence_id.write({'suffix': '/FRE'})
    print('Secuencia existente -> /FRE')

bom = env['mrp.bom'].sudo().with_context(active_test=False).search([('product_tmpl_id', '=', t.id)], limit=1)
assert bom, 'DMFRE01 sin BoM'
if not bom.active:
    bom.active = True; print('BoM reactivada')
bom.write({'product_qty': 1.0})
bom.bom_line_ids.unlink()
for code, qty in [('SPHMC42', 0.40), ('MPCAR42', 1), ('STDSC01', 1), ('STBPR01', 1), ('STGOT02', 1), ('MPBOL01', 1)]:
    env['mrp.bom.line'].sudo().create({'bom_id': bom.id, 'product_id': pp(code).id, 'product_qty': qty})
print('Lineas BoM:', len(bom.bom_line_ids), '| product_qty:', bom.product_qty)

bom.operation_ids.unlink()
ops = [
    (5,  'Surtido de materiales - FACTOR REUMATOIDE',                        'Almacén Materia Prima',    False, False),
    (10, 'Serigrafiado de empaque primario - FACTOR REUMATOIDE',            'Acondicionado 2',          True,  True),
    (20, 'Corte de hojas maestras compradas - FACTOR REUMATOIDE',           'Laminado, Secado y Corte', True,  False),
    (30, 'Encartuchado de tiras - FACTOR REUMATOIDE',                       'Encartuchado',             True,  True),
    (50, 'Acondicionado 1 - FACTOR REUMATOIDE',                             'Acondicionado 1',          True,  False),
    (55, 'Sellado de Empaque primario - FACTOR REUMATOIDE',                 'Acondicionado 1',          True,  False),
    (60, 'Acondicionado 2 - FACTOR REUMATOIDE',                             'Acondicionado 2',          True,  False),
    (70, 'Resguardo de producto en espera de analisis - FACTOR REUMATOIDE', 'Almacen Temporal PT',      True,  False),
]
for s, name, centro, sup, insp in ops:
    env['mrp.routing.workcenter'].sudo().create({
        'bom_id': bom.id, 'sequence': s, 'name': name, 'workcenter_id': wc(centro),
        'amunet_requires_supervision': sup, 'amunet_requires_inspection': insp,
        'time_cycle_manual': 1, 'time_mode': 'manual'})
print('Operaciones:', len(bom.operation_ids))

Pres = env['amunet.packaging.presentation'].sudo()
Pres.search([('product_tmpl_id', '=', t.id)]).unlink()
for size in [5, 20]:
    comps = [(0, 0, {'product_id': pp(c).id, 'qty_per_box': 1, 'sequence': (i + 1) * 10})
             for i, c in enumerate(['MICAJ01', 'MIMAN01'])]
    Pres.create({'product_tmpl_id': t.id, 'name': 'Caja con %d pruebas' % size,
                 'package_qty': size, 'is_authorized': True,
                 'authorization_source': 'manual', 'component_ids': comps})
print('Presentaciones:', len(Pres.search([('product_tmpl_id', '=', t.id)])))

env.cr.commit()
print('LISTO')
