# Completa el producto terminado DIAM-023 (COVID 19 IgG/IgM) linea corta:
#  - Folio MO -> /CAB (hoy /C19)
#  - BoM (por pieza): SPHMC02 0.40cm, MPCAR02 1, STDSC01 1, STGOT01 1, MPBOL01 1
#  - Ruta 8 pasos estandar (con supervision/inspeccion) igual que ROTADENET
#  - Presentaciones 5 y 10 pzas: MICAJ01 + MIMAN01 + STBAC01 (1 c/u por caja)
# El vial STBAC01 va en EMPAQUE (por caja), no en la receta (spec de Fernando).
# Autorizado por Fernando 2026-07-23.
Tmpl = env['product.template'].sudo()
Prod = env['product.product'].sudo()

t = Tmpl.search([('default_code', '=', 'DIAM-023')], limit=1)
assert t, 'DIAM-023 no existe'
bom = env['mrp.bom'].sudo().with_context(active_test=False).search([('product_tmpl_id', '=', t.id)], limit=1)
assert bom, 'DIAM-023 sin BoM'
if not bom.active:
    bom.active = True
    print('BoM reactivada (estaba archivada)')

def pp(code):
    p = Prod.search([('default_code', '=', code)], limit=1)
    assert p, 'falta producto %s' % code
    return p

# 1) Folio /CAB
env['ir.sequence'].sudo().browse(2146).write({'suffix': '/CAB'})
print('Folio ->', env['ir.sequence'].browse(2146).prefix + '##' + env['ir.sequence'].browse(2146).suffix)

# 2) BoM: limpiar y cargar receta por pieza
bom.bom_line_ids.unlink()
receta = [('SPHMC02', 0.40), ('MPCAR02', 1), ('STDSC01', 1), ('STGOT01', 1), ('MPBOL01', 1)]
for code, qty in receta:
    env['mrp.bom.line'].sudo().create({'bom_id': bom.id, 'product_id': pp(code).id, 'product_qty': qty})
print('Lineas BoM:', len(bom.bom_line_ids))

# 3) Ruta 8 pasos (plantilla ROTADENET)
bom.operation_ids.unlink()
ops = [
    (5,  'Surtido de materiales - COVID19 IgG/IgM',                    5,  False, False),
    (10, 'Serigrafiado de empaque primario - COVID19 IgG/IgM',        14, True,  True),
    (20, 'Corte de hojas maestras compradas - COVID19 IgG/IgM',       7,  True,  False),
    (30, 'Encartuchado de tiras - COVID19 IgG/IgM',                   15, True,  True),
    (50, 'Acondicionado 1 - COVID19 IgG/IgM',                         13, True,  False),
    (55, 'Sellado de Empaque primario - COVID19 IgG/IgM',             13, True,  False),
    (60, 'Acondicionado 2 - COVID19 IgG/IgM',                         14, True,  False),
    (70, 'Resguardo de producto en espera de analisis - COVID19 IgG/IgM', 16, True, False),
]
for seq, name, wc, sup, insp in ops:
    env['mrp.routing.workcenter'].sudo().create({
        'bom_id': bom.id, 'sequence': seq, 'name': name, 'workcenter_id': wc,
        'amunet_requires_supervision': sup, 'amunet_requires_inspection': insp,
        'time_cycle_manual': 1, 'time_mode': 'manual'})
print('Operaciones:', len(bom.operation_ids))

# 4) Presentaciones 5 y 10 (empaque por caja: caja + instructivo + vial)
Pres = env['amunet.packaging.presentation'].sudo()
Pres.search([('product_tmpl_id', '=', t.id)]).unlink()
empaque = ['MICAJ01', 'MIMAN01', 'STBAC01']
for size in [5, 10]:
    comps = [(0, 0, {'product_id': pp(c).id, 'qty_per_box': 1, 'sequence': (i + 1) * 10}) for i, c in enumerate(empaque)]
    Pres.create({'product_tmpl_id': t.id, 'name': 'Caja con %d pruebas' % size,
                 'package_qty': size, 'is_authorized': True,
                 'authorization_source': 'manual', 'component_ids': comps})
print('Presentaciones:', len(Pres.search([('product_tmpl_id', '=', t.id)])))

env.cr.commit()
print('LISTO')
