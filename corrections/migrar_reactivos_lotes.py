# -*- coding: utf-8 -*-
# Migracion Almacen MP -> produccion: 34 reactivos nuevos + 54 lotes + existencias.
# Origen: capturado en staging por 'almacenmp' (Karla), primera parte. Autorizado
# por Fernando el 2026-07-16. Replica staging TAL CUAL (config leida de staging via
# /tmp/reactivos.json). Idempotente: no duplica productos/lotes ni re-ajusta si ya
# coincide la existencia. Productos se crean CON clave (default_code) => no dispara
# el candado de codificacion (que solo bloquea altas sin clave).
import json

data = json.load(open('/tmp/reactivos.json'))
assert len(data['products']) == 34, 'esperaba 34 productos, hay %s' % len(data['products'])
assert len(data['lots']) == 54, 'esperaba 54 lotes, hay %s' % len(data['lots'])

Categ = env['product.category']; Tmpl = env['product.template']
Prod = env['product.product']; Lot = env['stock.lot']
Quant = env['stock.quant']; Factory = env['amunet.lot.factory']; Uom = env['uom.uom']
LOC_ID = 5  # AMP/Existencias en amunet_prod

categ = Categ.search([('complete_name', '=', 'Materia prima / Reactivo')], limit=1)
assert categ, 'falta categoria Materia prima / Reactivo en prod'

_uom = {}
def get_uom(name):
    if name not in _uom:
        u = Uom.search([('name', '=', name)], limit=1)
        assert u, 'UoM no encontrada en prod: %s' % name
        _uom[name] = u
    return _uom[name]

# 1) Productos (34)
n_prod = 0
for p in data['products']:
    if Tmpl.search([('default_code', '=', p['default_code'])], limit=1):
        continue
    Tmpl.create({
        'name': p['name'], 'default_code': p['default_code'],
        'type': p.get('type', 'consu'), 'is_storable': p.get('is_storable', True),
        'tracking': p.get('tracking', 'lot'),
        'uom_id': get_uom(p['uom']).id, 'categ_id': categ.id,
        'sale_ok': p.get('sale_ok', True), 'purchase_ok': p.get('purchase_ok', True),
        'use_expiration_date': p.get('use_expiration_date', True),
        'expiration_time': p.get('expiration_time', 0), 'use_time': p.get('use_time', 0),
        'removal_time': p.get('removal_time', 0), 'alert_time': p.get('alert_time', 0),
        'amunet_req_quality_control': p.get('req_qc', True),
        'amunet_requires_quarantine': p.get('req_quarantine', False),
    })
    n_prod += 1
    print('[PROD] creado %s (%s)' % (p['default_code'], p['name']))

# 2) Lotes + lote proveedor + existencias
n_lot = 0; n_fac = 0; n_adj = 0
for l in data['lots']:
    variant = Prod.search([('default_code', '=', l['product'])], limit=1)
    if not variant:
        print('[WARN] sin producto en prod: %s' % l['product']); continue
    fac = False
    if l.get('factory_lot'):
        fac = Factory.search([('name', '=', l['factory_lot'])], limit=1)
        if not fac:
            fac = Factory.create({'name': l['factory_lot']})
            n_fac += 1
    lot = Lot.search([('name', '=', l['lot']), ('product_id', '=', variant.id)], limit=1)
    lot_vals = {}
    if l.get('expiration_date'):
        # ISO trae 'YYYY-MM-DDTHH:MM:SS'; Odoo espera 'YYYY-MM-DD HH:MM:SS'
        lot_vals['expiration_date'] = l['expiration_date'].replace('T', ' ')
    if fac:
        lot_vals['factory_lot_id'] = fac.id
    if not lot:
        lot = Lot.create(dict(name=l['lot'], product_id=variant.id,
                              company_id=env.company.id, **lot_vals))
        n_lot += 1
        print('[LOTE] creado %s (%s)' % (l['lot'], l['product']))
    elif lot_vals:
        lot.write(lot_vals)
    qty = l.get('qty', 0) or 0
    actual = sum(Quant.search([('product_id', '=', variant.id),
                               ('lot_id', '=', lot.id),
                               ('location_id', '=', LOC_ID)]).mapped('quantity'))
    if abs(actual - qty) < 0.0001:
        continue
    q = Quant.with_context(inventory_mode=True).create({
        'product_id': variant.id, 'location_id': LOC_ID,
        'lot_id': lot.id, 'inventory_quantity': qty})
    q.action_apply_inventory()
    n_adj += 1
    print('[EXIST] %s/%s -> %s (antes %s)' % (l['product'], l['lot'], qty, actual))

env.cr.commit()
print('RESUMEN: productos_nuevos=%s lotes_nuevos=%s factory_nuevos=%s ajustes_inv=%s'
      % (n_prod, n_lot, n_fac, n_adj))
