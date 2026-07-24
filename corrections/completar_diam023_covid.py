# Completa el producto terminado DIAM-023 (COVID 19 IgG/IgM) linea corta en PROD.
# Portable (busca por default_code / nombre, no por id):
#  - Folio MO -> /CAB (hoy /C19)
#  - BoM (por pieza): SPHMC02 0.40cm, MPCAR02 1, STDSC01 1, STGOT01 1, MPBOL01 1
#  - Ruta 8 pasos estandar (supervision/inspeccion) igual que ROTADENET
#  - Presentaciones 5 y 10 pzas: MICAJ01 + MIMAN01 + STBAC01 (1 c/u por caja)
# El vial STBAC01 va en EMPAQUE (por caja), no en la receta. Validado en staging.
# Autorizado por Fernando 2026-07-23.
Prod = env['product.product'].sudo()
t = env['product.template'].sudo().search([('default_code', '=', 'DIAM-023')], limit=1)
assert t, 'DIAM-023 no existe'

def pp(code):
    p = Prod.search([('default_code', '=', code)], limit=1)
    assert p, 'falta producto %s' % code
    return p

def wc(name):
    w = env['mrp.workcenter'].sudo().search([('name', '=', name)], limit=1)
    assert w, 'falta centro %s' % name
    return w.id

# 1) Folio /CAB (via la secuencia del propio producto)
seq = t.mo_sequence_id
assert seq, 'DIAM-023 sin secuencia de folio'
seq.write({'suffix': '/CAB'})
print('Folio ->', seq.prefix + '##' + seq.suffix)

# 2) BoM (reactivar si archivada) + receta por pieza
bom = env['mrp.bom'].sudo().with_context(active_test=False).search([('product_tmpl_id', '=', t.id)], limit=1)
assert bom, 'DIAM-023 sin BoM'
if not bom.active:
    bom.active = True
    print('BoM reactivada')
bom.bom_line_ids.unlink()
for code, qty in [('SPHMC02', 0.40), ('MPCAR02', 1), ('STDSC01', 1), ('STGOT01', 1), ('MPBOL01', 1)]:
    env['mrp.bom.line'].sudo().create({'bom_id': bom.id, 'product_id': pp(code).id, 'product_qty': qty})
print('Lineas BoM:', len(bom.bom_line_ids))

# 3) Ruta 8 pasos (centros por nombre)
bom.operation_ids.unlink()
ops = [
    (5,  'Surtido de materiales - COVID19 IgG/IgM',                        'Almacén Materia Prima',    False, False),
    (10, 'Serigrafiado de empaque primario - COVID19 IgG/IgM',            'Acondicionado 2',          True,  True),
    (20, 'Corte de hojas maestras compradas - COVID19 IgG/IgM',           'Laminado, Secado y Corte', True,  False),
    (30, 'Encartuchado de tiras - COVID19 IgG/IgM',                       'Encartuchado',             True,  True),
    (50, 'Acondicionado 1 - COVID19 IgG/IgM',                             'Acondicionado 1',          True,  False),
    (55, 'Sellado de Empaque primario - COVID19 IgG/IgM',                 'Acondicionado 1',          True,  False),
    (60, 'Acondicionado 2 - COVID19 IgG/IgM',                             'Acondicionado 2',          True,  False),
    (70, 'Resguardo de producto en espera de analisis - COVID19 IgG/IgM', 'Almacen Temporal PT',      True,  False),
]
for s, name, centro, sup, insp in ops:
    env['mrp.routing.workcenter'].sudo().create({
        'bom_id': bom.id, 'sequence': s, 'name': name, 'workcenter_id': wc(centro),
        'amunet_requires_supervision': sup, 'amunet_requires_inspection': insp,
        'time_cycle_manual': 1, 'time_mode': 'manual'})
print('Operaciones:', len(bom.operation_ids))

# 4) Presentaciones 5 y 10 (empaque por caja)
Pres = env['amunet.packaging.presentation'].sudo()
Pres.search([('product_tmpl_id', '=', t.id)]).unlink()
for size in [5, 10]:
    comps = [(0, 0, {'product_id': pp(c).id, 'qty_per_box': 1, 'sequence': (i + 1) * 10})
             for i, c in enumerate(['MICAJ01', 'MIMAN01', 'STBAC01'])]
    Pres.create({'product_tmpl_id': t.id, 'name': 'Caja con %d pruebas' % size,
                 'package_qty': size, 'is_authorized': True,
                 'authorization_source': 'manual', 'component_ids': comps})
print('Presentaciones:', len(Pres.search([('product_tmpl_id', '=', t.id)])))

env.cr.commit()
print('LISTO')
