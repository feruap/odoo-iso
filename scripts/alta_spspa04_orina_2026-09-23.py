# Alta de la Solucion de pretratamiento para almohadilla de muestra ORINA,
# cuarta de la familia SPSPA, a partir de la instruccion de trabajo que entrego
# Mery el 23-sep-2026. No se toca ninguna de las tres existentes.
#
# CLAVES PROPUESTAS (pendientes de que Stacy las valide):
#   SPSPA04   la solucion   (SPSPA01-03 ya existen, es la misma para otra muestra)
#   MPREC98   el surfactante S17, que no estaba dado de alta (ultimo usado MPREC97)
T = env['product.template'].with_context(amunet_alta_autorizada=True)
P = env['product.product']

modelo = T.search([('default_code', '=', 'SPSPA02')], limit=1)
assert modelo, 'No existe SPSPA02, que es el modelo de configuracion'
uom_L  = modelo.uom_id
uom_ml = env['uom.uom'].browse(11)
uom_g  = env['uom.uom'].browse(46)
assert uom_ml.name == 'ml' and uom_g.name == 'g', 'Unidades inesperadas'

# --- 1. El surfactante S17 -------------------------------------------------
modelo_mp = T.search([('default_code', '=', 'MPREC15')], limit=1)
assert modelo_mp, 'No existe MPREC15 (S9), que es el modelo del surfactante'
s17 = T.search([('default_code', '=', 'MPREC98')], limit=1)
if not s17:
    s17 = T.create({
        'default_code': 'MPREC98',
        'name': 'S17',
        'categ_id': modelo_mp.categ_id.id,
        'uom_id': uom_ml.id,
        'type': 'consu',
        'is_storable': True,
        'tracking': 'lot',
        'use_expiration_date': True,
        'purchase_ok': True,
        'sale_ok': False,
    })
    s17.with_context(lang='es_MX', amunet_alta_autorizada=True).name = 'S17'
    print('CREADO  MPREC98  S17  (surfactante, ml)')
else:
    print('ya existia MPREC98')

# --- 2. La solucion --------------------------------------------------------
NOMBRE = 'Solución de pretratamiento para almohadilla de muestra orina'
sol = T.search([('default_code', '=', 'SPSPA04')], limit=1)
if not sol:
    sol = T.create({
        'default_code': 'SPSPA04',
        'name': NOMBRE,
        'categ_id': modelo.categ_id.id,
        'uom_id': uom_L.id,
        'type': modelo.type,
        'is_storable': modelo.is_storable,
        'tracking': 'lot',
        'use_expiration_date': True,
        'purchase_ok': modelo.purchase_ok,
        'sale_ok': modelo.sale_ok,
        'amunet_expiration_text': '1 Meses',
        'amunet_ph_requerido': True,
        'amunet_initial_ph': 8,
        'amunet_ph_adj_range_text': '± 0.05',
        'amunet_req_quality_control': modelo.amunet_req_quality_control,
        'qc_required': modelo.qc_required,
    })
    sol.with_context(lang='es_MX', amunet_alta_autorizada=True).name = NOMBRE
    print('CREADO  SPSPA04  %s' % NOMBRE)
else:
    print('ya existia SPSPA04')

# --- 3. La receta ----------------------------------------------------------
# Rinde 1 L. El agua sale de 1000 ml menos los LIQUIDOS (3.3 de S17 + 3.4 de
# HCl); los solidos no restan volumen. Es el mismo criterio de SPSPA01/02/03.
RECETA = [
    ('MPREC10', 38.1, uom_g),    # Tris-base
    ('MPREC03',  2.0, uom_g),    # Caseina lactica
    ('MPREC11', 10.0, uom_g),    # Polivinilpirrolidona (PVP)
    ('MPREC98',  3.3, uom_ml),   # S17
    ('MPREC05',  5.0, uom_g),    # Cloruro de sodio
    ('SPSAC01',  3.4, uom_ml),   # Solucion HCl 6 M (ajuste de pH a 8 +- 0.05)
    ('MPATR01', 993.3, uom_ml),  # Agua tridestilada  c.b.p. 1 L
]
bom = env['mrp.bom'].search([('product_tmpl_id', '=', sol.id), ('active', '=', True)], limit=1)
if not bom:
    lineas = []
    for i, (clave, cant, uom) in enumerate(RECETA):
        comp = P.search([('default_code', '=', clave)], limit=1)
        assert comp, 'Falta el componente %s' % clave
        lineas.append((0, 0, {'product_id': comp.id, 'product_qty': cant,
                              'product_uom_id': uom.id, 'sequence': (i + 1) * 10}))
    bom = env['mrp.bom'].create({
        'product_tmpl_id': sol.id, 'product_qty': 1.0, 'product_uom_id': uom_L.id,
        'type': 'normal', 'bom_line_ids': lineas,
    })
    print('CREADA receta, rinde 1 L, %s componentes' % len(RECETA))
else:
    print('ya existia receta')

env.cr.commit()
print('\n--- SPSPA04 ---')
print('  unidad=%s  lote=%s  caducidad=%s  pH=%s %s  requiere analisis=%s'
      % (sol.uom_id.name, sol.tracking, sol.amunet_expiration_text,
         sol.amunet_initial_ph, sol.amunet_ph_adj_range_text,
         sol.amunet_req_quality_control))
for l in bom.bom_line_ids.sorted('sequence'):
    print('  %-9s %-34s %8s %s' % (l.product_id.default_code,
          l.product_id.name[:34], l.product_qty, l.product_uom_id.name))
