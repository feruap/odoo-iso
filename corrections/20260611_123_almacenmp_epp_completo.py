# Configuración completa EPP para Almacén MP
# Solicitud de Karla (almacen.mp) — aprobado por Mery para producción
# Incluye: categoría, 8 productos almacenables, reglas de reabastecimiento,
# ruta de compra automática y notificación por correo a Verónica Ortiz.

# --- 1. Categoría Consumible / EPP ---
cat_consumible = env['product.category'].search([('complete_name', '=', 'Consumible')], limit=1)
if not cat_consumible:
    print("ERROR: No se encontró categoría 'Consumible'")
else:
    cat_epp = env['product.category'].search([('complete_name', '=', 'Consumible / EPP')], limit=1)
    if not cat_epp:
        cat_epp = env['product.category'].create({
            'name': 'EPP',
            'parent_id': cat_consumible.id,
        })
        print("Categoría creada: Consumible / EPP (id=" + str(cat_epp.id) + ")")
    else:
        print("Categoría ya existe: Consumible / EPP (id=" + str(cat_epp.id) + ")")

# --- 2. Productos EPP almacenables ---
uom_units = env['uom.uom'].search([('name', '=', 'Units')], limit=1)
if not uom_units:
    uom_units = env['uom.uom'].search([('name', '=', 'Unidades')], limit=1)

productos_epp = [
    {'name': 'Guantes de Nitrilo Extra Chicos', 'default_code': 'COGEC01'},
    {'name': 'Guantes de Nitrilo Chicos',       'default_code': 'COGCH01'},
    {'name': 'Guantes de Nitrilo Medianos',     'default_code': 'COGME01'},
    {'name': 'Guantes de Nitrilo Grandes',      'default_code': 'COGGR01'},
    {'name': 'Cofia',                           'default_code': 'COCOF01'},
    {'name': 'Sanitas',                         'default_code': 'COSAN01'},
    {'name': 'Cubrebocas',                      'default_code': 'COCBO01'},
    {'name': 'Bata Desechable',                 'default_code': 'COBDE01'},
]

for p in productos_epp:
    existe = env['product.template'].search([('default_code', '=', p['default_code'])], limit=1)
    if existe:
        existe.write({'categ_id': cat_epp.id, 'is_storable': True, 'uom_id': uom_units.id})
        print("Actualizado: " + existe.name)
    else:
        env['product.template'].create({
            'name': p['name'],
            'default_code': p['default_code'],
            'categ_id': cat_epp.id,
            'uom_id': uom_units.id,
            'type': 'consu',
            'is_storable': True,
            'purchase_ok': True,
            'sale_ok': False,
        })
        print("Creado: " + p['name'])

# --- 3. Ruta de compra en productos EPP ---
ruta_compra = env['stock.route'].search([('name', 'ilike', 'Buy')], limit=1)
if not ruta_compra:
    ruta_compra = env['stock.route'].search([('name', 'ilike', 'Comprar')], limit=1)
refs = [p['default_code'] for p in productos_epp]
pts = env['product.template'].search([('default_code', 'in', refs)])
for pt in pts:
    if ruta_compra not in pt.route_ids:
        pt.route_ids = [(4, ruta_compra.id)]
print("Ruta Comprar activada en " + str(len(pts)) + " productos")

# --- 4. Reglas de reabastecimiento (mínimos y máximos) ---
wh_amp = env['stock.warehouse'].search([('code', '=', 'AMP')], limit=1)
if not wh_amp:
    wh_amp = env['stock.warehouse'].search([('lot_stock_id.complete_name', 'ilike', 'AMP')], limit=1)

reglas = [
    {'ref': 'COCOF01', 'min': 1,  'max': 5},
    {'ref': 'COSAN01', 'min': 10, 'max': 60},
    {'ref': 'COCBO01', 'min': 1,  'max': 5},
    {'ref': 'COBDE01', 'min': 1,  'max': 3},
    {'ref': 'COGEC01', 'min': 1,  'max': 3},
    {'ref': 'COGCH01', 'min': 3,  'max': 12},
    {'ref': 'COGME01', 'min': 3,  'max': 10},
    {'ref': 'COGGR01', 'min': 1,  'max': 7},
]

for r in reglas:
    pt = env['product.template'].search([('default_code', '=', r['ref'])], limit=1)
    if not pt:
        continue
    pp = pt.product_variant_ids[:1]
    op = env['stock.warehouse.orderpoint'].search([
        ('product_id', '=', pp.id),
        ('warehouse_id', '=', wh_amp.id),
    ], limit=1)
    if op:
        op.write({'product_min_qty': r['min'], 'product_max_qty': r['max']})
    else:
        env['stock.warehouse.orderpoint'].create({
            'product_id': pp.id,
            'warehouse_id': wh_amp.id,
            'location_id': wh_amp.lot_stock_id.id,
            'product_min_qty': r['min'],
            'product_max_qty': r['max'],
        })
    print("Regla OK: " + pt.name + " min=" + str(r['min']) + " max=" + str(r['max']))

# --- 5. Automatización: correo a Verónica al crear OC con EPP ---
veronica = env['res.users'].search([('login', '=', 'supalmacen@amunet.com.mx')], limit=1)
if not veronica:
    print("AVISO: No se encontró usuario supalmacen@amunet.com.mx — omitiendo automatización")
else:
    model_po = env['ir.model'].search([('model', '=', 'purchase.order')], limit=1)
    auto_existente = env['base.automation'].search([
        ('name', '=', 'Notificar EPP a Verónica al crear OC')
    ], limit=1)
    if not auto_existente:
        codigo = """
for record in records:
    epp_lines = record.order_line.filtered(
        lambda l: l.product_id.categ_id.complete_name == 'Consumible / EPP'
    )
    if not epp_lines:
        continue
    productos_epp = ', '.join(epp_lines.mapped('product_id.name'))
    record.message_post(
        body='<b>Solicitud de reabastecimiento EPP generada automáticamente.</b><br/>Productos: ' + productos_epp,
        partner_ids=[%d],
        message_type='email',
        subtype_xmlid='mail.mt_comment',
    )
""" % veronica.partner_id.id
        accion = env['ir.actions.server'].create({
            'name': 'Notificar EPP a Verónica',
            'model_id': model_po.id,
            'state': 'code',
            'code': codigo,
        })
        env['base.automation'].create({
            'name': 'Notificar EPP a Verónica al crear OC',
            'model_id': model_po.id,
            'trigger': 'on_create',
            'action_server_ids': [(4, accion.id)],
            'active': True,
        })
        print("Automatización de correo creada para Verónica")
    else:
        print("Automatización ya existe")

print("SCRIPT COMPLETADO OK")
