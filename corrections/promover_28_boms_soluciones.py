# -*- coding: utf-8 -*-
# Promueve a produccion las 28 recetas (BoM) de soluciones desde staging.
# Autorizado por Fernando 2026-07-11. Incluye:
#  - 2 productos nuevos: SPCDS01 (Citrato de sodio 1%), SPACL01 (Acido cloroaurico 1%).
#  - config pH/caducidad/flags en los 28 productos con receta.
#  - 28 BoMs con sus lineas (componentes resueltos por clave, UoM por nombre).
# Idempotente: no crea productos/BoMs que ya existan. Datos en /tmp/boms.json
# (extraidos de staging; IDs de UoM difieren entre entornos -> se resuelve por nombre).
import json

data = json.load(open('/tmp/boms.json'))
Tmpl = env['product.template']
Prod = env['product.product']
Uom = env['uom.uom']
Bom = env['mrp.bom']
Categ = env['product.category']

CFG_FIELDS = ['amunet_initial_ph', 'amunet_expiration_text', 'amunet_req_history_log',
              'amunet_req_calculations', 'amunet_req_dilution', 'amunet_req_aforar',
              'amunet_req_quality_control', 'amunet_ph_adj_range_text', 'amunet_weighing_range_text']

_uom_cache = {}
def uom_by_name(name):
    if name not in _uom_cache:
        _uom_cache[name] = Uom.search([('name', '=', name)], limit=1)
    return _uom_cache[name]

def prod_by_code(code):
    return Prod.search([('default_code', '=', code)], limit=1)

# 1) Crear los 2 productos nuevos
n_prod = 0
for p in data['nuevos']:
    if prod_by_code(p['default_code']):
        print("  [PROD] %s ya existe" % p['default_code'])
        continue
    categ = Categ.search([('complete_name', '=', p['categ'])], limit=1)
    Tmpl.create({
        'name': p['name'],
        'default_code': p['default_code'],
        'categ_id': categ.id,
        'uom_id': uom_by_name(p['uom']).id,
        'tracking': p['tracking'],
        'type': p['type'],
        'is_storable': p.get('is_storable', True),
    })
    n_prod += 1
    print("  [PROD] creado %s (%s)" % (p['default_code'], p['name']))

# 2) Config pH/caducidad/flags en los 28
n_cfg = 0
for cfg in data['config']:
    t = Tmpl.search([('default_code', '=', cfg['default_code'])], limit=1)
    if not t:
        print("  [CFG] %s no existe, salto" % cfg['default_code'])
        continue
    vals = {f: cfg[f] for f in CFG_FIELDS if f in cfg}
    t.write(vals)
    n_cfg += 1

# 3) Crear las 28 BoMs (idempotente por producto)
n_bom = 0
n_skip = 0
for b in data['boms']:
    t = Tmpl.search([('default_code', '=', b['product_code'])], limit=1)
    if not t:
        print("  [BOM] producto %s no existe, salto" % b['product_code'])
        continue
    if Bom.search([('product_tmpl_id', '=', t.id)], limit=1):
        n_skip += 1
        continue
    lines = []
    faltan = []
    for l in b['lines']:
        cp = prod_by_code(l['comp_code'])
        if not cp:
            faltan.append(l['comp_code'])
            continue
        lines.append((0, 0, {
            'product_id': cp.id,
            'product_qty': l['qty'],
            'product_uom_id': uom_by_name(l['uom']).id,
        }))
    if faltan:
        print("  [BOM] %s: faltan componentes %s -> NO se crea" % (b['product_code'], faltan))
        continue
    Bom.create({
        'product_tmpl_id': t.id,
        'product_qty': b['product_qty'],
        'product_uom_id': uom_by_name(b['product_uom']).id,
        'type': b['type'],
        'bom_line_ids': lines,
    })
    n_bom += 1
    print("  [BOM] creada %s (%s comp)" % (b['product_code'], len(lines)))

env.cr.commit()
print("RESUMEN: productos_nuevos=%s config=%s boms_creadas=%s boms_saltadas=%s" % (n_prod, n_cfg, n_bom, n_skip))
