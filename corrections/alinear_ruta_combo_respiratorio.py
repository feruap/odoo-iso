# Alinea la ruta de fabricacion de DMCRD01 (Combo Respiratorio) a la ruta estandar
# de linea corta de 8 pasos (igual que COVID/TIFOIDEA/ROTADENET). Reemplaza la ruta
# de 9 pasos que tenia (con "Control en proceso lateral flow", "Impresion/Etiquetado",
# "Colocacion en empaque", "Sellado de bolsa/tubo"). Solo afecta ordenes FUTURAS; las
# existentes conservan sus workorders. Autorizado por Fernando 2026-07-23.
t = env['product.template'].sudo().search([('default_code', '=', 'DMCRD01')], limit=1)
assert t, 'DMCRD01 no existe'
bom = env['mrp.bom'].sudo().with_context(active_test=False).search([('product_tmpl_id', '=', t.id)], limit=1)
assert bom, 'DMCRD01 sin BoM'

def wc(name):
    w = env['mrp.workcenter'].sudo().search([('name', '=', name)], limit=1)
    assert w, 'falta centro %s' % name
    return w.id

print('Operaciones antes:', len(bom.operation_ids))
bom.operation_ids.unlink()
ops = [
    (5,  'Surtido de materiales - Combo Respiratorio',                        'Almacén Materia Prima',    False, False),
    (10, 'Serigrafiado de empaque primario - Combo Respiratorio',            'Acondicionado 2',          True,  True),
    (20, 'Corte de hojas maestras compradas - Combo Respiratorio',           'Laminado, Secado y Corte', True,  False),
    (30, 'Encartuchado de tiras - Combo Respiratorio',                       'Encartuchado',             True,  True),
    (50, 'Acondicionado 1 - Combo Respiratorio',                             'Acondicionado 1',          True,  False),
    (55, 'Sellado de Empaque primario - Combo Respiratorio',                 'Acondicionado 1',          True,  False),
    (60, 'Acondicionado 2 - Combo Respiratorio',                             'Acondicionado 2',          True,  False),
    (70, 'Resguardo de producto en espera de analisis - Combo Respiratorio', 'Almacen Temporal PT',      True,  False),
]
for s, name, centro, sup, insp in ops:
    env['mrp.routing.workcenter'].sudo().create({
        'bom_id': bom.id, 'sequence': s, 'name': name, 'workcenter_id': wc(centro),
        'amunet_requires_supervision': sup, 'amunet_requires_inspection': insp,
        'time_cycle_manual': 1, 'time_mode': 'manual'})
env.cr.commit()
print('Operaciones despues:', len(bom.operation_ids))
for w in bom.operation_ids.sorted('sequence'):
    print('  ', w.sequence, w.name)
print('LISTO')
