# Completa el producto terminado DMTIF01 (TIFOIDEA IgG/IgM) linea corta.
# Portable (por default_code / nombre de centro):
#  - Nombre corto "TIFOIDEA IgG/IgM" (en_US + es_MX)
#  - Crea secuencia de folio MO /TIF (no tenia) y la liga
#  - BoM (por pieza): SPHMC43 0.40cm, MPCAR43 1, STGOT05 1, STDSC01 1, MPBOL01 1
#    (reemplaza la BoM 46 actual, que tenia cantidades de 70 + gotero equivocado + vial)
#  - Ruta 8 pasos estandar (supervision/inspeccion) igual que ROTADENET/COVID
#  - Presentaciones 2 y 20 pzas: MICAJ01 + STBAC01 + MIMAN01 (1 c/u por caja)
# Autorizado por Fernando 2026-07-23.
Prod = env['product.product'].sudo()
t = env['product.template'].sudo().search([('default_code', '=', 'DMTIF01')], limit=1)
assert t, 'DMTIF01 no existe'

def pp(code):
    p = Prod.search([('default_code', '=', code)], limit=1)
    assert p, 'falta producto %s' % code
    return p

def wc(name):
    w = env['mrp.workcenter'].sudo().search([('name', '=', name)], limit=1)
    assert w, 'falta centro %s' % name
    return w.id

# 1) Nombre corto (campo traducible -> ambos idiomas)
t.with_context(lang='en_US').write({'name': 'TIFOIDEA IgG/IgM'})
t.with_context(lang='es_MX').write({'name': 'TIFOIDEA IgG/IgM'})
print('Nombre:', t.with_context(lang='es_MX').name)

# 2) Secuencia de folio /TIF (crear y ligar si no existe)
if not t.mo_sequence_id:
    seq = env['ir.sequence'].sudo().create({
        'name': 'Folio MO TIFOIDEA (TIF)', 'prefix': '%(month)s%(y)s/', 'suffix': '/TIF',
        'padding': 2, 'number_next': 1, 'implementation': 'standard', 'company_id': 1})
    t.mo_sequence_id = seq.id
    print('Secuencia creada:', seq.prefix + '##' + seq.suffix)
else:
    t.mo_sequence_id.write({'suffix': '/TIF'})
    print('Secuencia existente -> /TIF')

# 3) BoM (reactivar si hace falta) + receta por pieza
bom = env['mrp.bom'].sudo().with_context(active_test=False).search([('product_tmpl_id', '=', t.id)], limit=1)
assert bom, 'DMTIF01 sin BoM'
if not bom.active:
    bom.active = True
    print('BoM reactivada')
bom.bom_line_ids.unlink()
for code, qty in [('SPHMC43', 0.40), ('MPCAR43', 1), ('STGOT05', 1), ('STDSC01', 1), ('MPBOL01', 1)]:
    env['mrp.bom.line'].sudo().create({'bom_id': bom.id, 'product_id': pp(code).id, 'product_qty': qty})
print('Lineas BoM:', len(bom.bom_line_ids))

# 4) Ruta 8 pasos
bom.operation_ids.unlink()
ops = [
    (5,  'Surtido de materiales - TIFOIDEA IgG/IgM',                        'Almacén Materia Prima',    False, False),
    (10, 'Serigrafiado de empaque primario - TIFOIDEA IgG/IgM',            'Acondicionado 2',          True,  True),
    (20, 'Corte de hojas maestras compradas - TIFOIDEA IgG/IgM',           'Laminado, Secado y Corte', True,  False),
    (30, 'Encartuchado de tiras - TIFOIDEA IgG/IgM',                       'Encartuchado',             True,  True),
    (50, 'Acondicionado 1 - TIFOIDEA IgG/IgM',                             'Acondicionado 1',          True,  False),
    (55, 'Sellado de Empaque primario - TIFOIDEA IgG/IgM',                 'Acondicionado 1',          True,  False),
    (60, 'Acondicionado 2 - TIFOIDEA IgG/IgM',                             'Acondicionado 2',          True,  False),
    (70, 'Resguardo de producto en espera de analisis - TIFOIDEA IgG/IgM', 'Almacen Temporal PT',      True,  False),
]
for s, name, centro, sup, insp in ops:
    env['mrp.routing.workcenter'].sudo().create({
        'bom_id': bom.id, 'sequence': s, 'name': name, 'workcenter_id': wc(centro),
        'amunet_requires_supervision': sup, 'amunet_requires_inspection': insp,
        'time_cycle_manual': 1, 'time_mode': 'manual'})
print('Operaciones:', len(bom.operation_ids))

# 5) Presentaciones 2 y 20
Pres = env['amunet.packaging.presentation'].sudo()
Pres.search([('product_tmpl_id', '=', t.id)]).unlink()
for size in [2, 20]:
    comps = [(0, 0, {'product_id': pp(c).id, 'qty_per_box': 1, 'sequence': (i + 1) * 10})
             for i, c in enumerate(['MICAJ01', 'STBAC01', 'MIMAN01'])]
    Pres.create({'product_tmpl_id': t.id, 'name': 'Caja con %d pruebas' % size,
                 'package_qty': size, 'is_authorized': True,
                 'authorization_source': 'manual', 'component_ids': comps})
print('Presentaciones:', len(Pres.search([('product_tmpl_id', '=', t.id)])))

env.cr.commit()
print('LISTO')
