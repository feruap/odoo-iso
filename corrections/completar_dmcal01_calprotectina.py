# Completa el producto terminado DMCAL01 (Calprotectina) linea corta. Portable.
#  - Nombre corto "CALPROTECTINA"
#  - Secuencia de folio MO /CAL
#  - BoM (por pieza): SPHMC55 0.40cm, MPCAR55 1, STGOT05 1, STBPR03 1, STDSC01 1, MPBOL01 1
#    (reemplaza BoM 52: product_qty=70, cartucho MPCAR76 equivocado, gotero STGOT01 equivocado)
#    Prueba de HECES -> vial STBPR03 va en la receta (no en empaque).
#  - Ruta 8 pasos estandar
#  - Presentaciones 5 y 20 pzas: MICAJ01 + MIMAN01 (sin vial en empaque)
# Autorizado por Fernando 2026-07-27.
Prod = env['product.product'].sudo()
t = env['product.template'].sudo().search([('default_code', '=', 'DMCAL01')], limit=1)
assert t, 'DMCAL01 no existe'

def pp(code):
    p = Prod.search([('default_code', '=', code)], limit=1)
    assert p, 'falta producto %s' % code
    return p

def wc(name):
    w = env['mrp.workcenter'].sudo().search([('name', '=', name)], limit=1)
    assert w, 'falta centro %s' % name
    return w.id

t.with_context(lang='en_US').write({'name': 'CALPROTECTINA'})
t.with_context(lang='es_MX').write({'name': 'CALPROTECTINA'})
print('Nombre:', t.with_context(lang='es_MX').name)

if not t.mo_sequence_id:
    seq = env['ir.sequence'].sudo().create({
        'name': 'Folio MO CALPROTECTINA', 'prefix': '%(month)s%(y)s/', 'suffix': '/CAL',
        'padding': 2, 'number_next': 1, 'implementation': 'standard', 'company_id': 1})
    t.mo_sequence_id = seq.id
    print('Secuencia creada:', seq.prefix + '##' + seq.suffix)
else:
    t.mo_sequence_id.write({'suffix': '/CAL'})
    print('Secuencia existente -> /CAL')

bom = env['mrp.bom'].sudo().with_context(active_test=False).search([('product_tmpl_id', '=', t.id)], limit=1)
assert bom, 'DMCAL01 sin BoM'
if not bom.active:
    bom.active = True; print('BoM reactivada')
bom.write({'product_qty': 1.0})
bom.bom_line_ids.unlink()
for code, qty in [('SPHMC55', 0.40), ('MPCAR55', 1), ('STGOT05', 1), ('STBPR03', 1), ('STDSC01', 1), ('MPBOL01', 1)]:
    env['mrp.bom.line'].sudo().create({'bom_id': bom.id, 'product_id': pp(code).id, 'product_qty': qty})
print('Lineas BoM:', len(bom.bom_line_ids), '| product_qty:', bom.product_qty)

bom.operation_ids.unlink()
ops = [
    (5,  'Surtido de materiales - CALPROTECTINA',                        'Almacén Materia Prima',    False, False),
    (10, 'Serigrafiado de empaque primario - CALPROTECTINA',            'Acondicionado 2',          True,  True),
    (20, 'Corte de hojas maestras compradas - CALPROTECTINA',           'Laminado, Secado y Corte', True,  False),
    (30, 'Encartuchado de tiras - CALPROTECTINA',                       'Encartuchado',             True,  True),
    (50, 'Acondicionado 1 - CALPROTECTINA',                             'Acondicionado 1',          True,  False),
    (55, 'Sellado de Empaque primario - CALPROTECTINA',                 'Acondicionado 1',          True,  False),
    (60, 'Acondicionado 2 - CALPROTECTINA',                             'Acondicionado 2',          True,  False),
    (70, 'Resguardo de producto en espera de analisis - CALPROTECTINA', 'Almacen Temporal PT',      True,  False),
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
