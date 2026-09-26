# Alta de tres soluciones simples, de las instrucciones de trabajo que entrego
# Mery el 23-sep-2026. Se configuran como sus hermanas (SPSAC01, SPSHS01/02,
# SPSAS01): unidad L, lote, sin pH requerido y SIN analisis de calidad, que es
# como estan todas las soluciones simples; solo las de corrimiento lo llevan.
#
# El agua sale de 1000 ml menos los LIQUIDOS; los solidos no restan volumen.
# Criterio verificado contra SPSAC01 (501.60 de acido + 498.40 de agua = 1000).
#
# CLAVES PROPUESTAS, pendientes de que Stacy valide las dos nuevas:
#   SPSAC02  HCl 0.1 M   -- familia existente, solo cambia el consecutivo
#   SPSCS01  NaCl 10%    -- Solucion Cloruro Sodio, patron de SPSHS y SPSAS
#   SPPVP01  PVP 5%      -- PVP es como se llama el reactivo en todos lados
T = env['product.template'].with_context(amunet_alta_autorizada=True)
P = env['product.product']

modelo = T.search([('default_code', '=', 'SPSAC01')], limit=1)
assert modelo, 'No existe SPSAC01, que es el modelo de configuracion'
uom_L  = modelo.uom_id
uom_ml = env['uom.uom'].browse(11)
uom_g  = env['uom.uom'].browse(46)
assert uom_ml.name == 'ml' and uom_g.name == 'g', 'Unidades inesperadas'

SOLUCIONES = [
    {'clave': 'SPSCS01',
     'nombre': 'Solución de Cloruro de Sodio 10%',
     'caducidad': '3 Meses',
     'receta': [('MPREC05', 100.0, uom_g),      # Cloruro de sodio
                ('MPATR01', 1000.0, uom_ml)]},  # agua c.b.p. 1 L (el solido no resta)
    {'clave': 'SPSAC02',
     'nombre': 'Solución de Ácido Clorhídrico 0.1 M',
     'caducidad': '6 Meses',
     'receta': [('MPREC37', 8.3, uom_ml),       # HCl 37%
                ('MPATR01', 991.7, uom_ml)]},   # 1000 - 8.3
    {'clave': 'SPPVP01',
     'nombre': 'Solución de Polivinilpirrolidona 5%',
     'caducidad': '3 Meses',
     'receta': [('MPREC11', 50.0, uom_g),       # PVP
                ('MPATR01', 1000.0, uom_ml)]},
]

for s in SOLUCIONES:
    # La clave se verifica AQUI, al crear, no al proponer: entre proponer y
    # crear alguien mas puede ocupar el consecutivo. Ya paso con MPREC98.
    existente = T.with_context(active_test=False).search(
        [('default_code', '=', s['clave'])], limit=1)
    if existente:
        print('  OCUPADA %s por %r -- NO se crea, hay que reasignar clave'
              % (s['clave'], existente.name))
        continue
    prod = T.create({
        'default_code': s['clave'], 'name': s['nombre'],
        'categ_id': modelo.categ_id.id, 'uom_id': uom_L.id,
        'type': modelo.type, 'is_storable': modelo.is_storable,
        'tracking': 'lot', 'use_expiration_date': True,
        'purchase_ok': modelo.purchase_ok, 'sale_ok': modelo.sale_ok,
        'amunet_expiration_text': s['caducidad'],
        'amunet_ph_requerido': False,
        'amunet_req_quality_control': modelo.amunet_req_quality_control,
        'qc_required': modelo.qc_required,
    })
    prod.with_context(lang='es_MX', amunet_alta_autorizada=True).name = s['nombre']
    lineas = []
    for i, (clave, cant, uom) in enumerate(s['receta']):
        comp = P.search([('default_code', '=', clave)], limit=1)
        assert comp, 'Falta el componente %s para %s' % (clave, s['clave'])
        lineas.append((0, 0, {'product_id': comp.id, 'product_qty': cant,
                              'product_uom_id': uom.id, 'sequence': (i + 1) * 10}))
    env['mrp.bom'].create({
        'product_tmpl_id': prod.id, 'product_qty': 1.0, 'product_uom_id': uom_L.id,
        'type': 'normal', 'bom_line_ids': lineas,
    })
    print('  CREADA %s  %s' % (s['clave'], s['nombre']))

env.cr.commit()
print('\n--- como quedaron ---')
for s in SOLUCIONES:
    p = T.search([('default_code', '=', s['clave'])], limit=1)
    if not p: continue
    b = env['mrp.bom'].search([('product_tmpl_id', '=', p.id), ('active', '=', True)], limit=1)
    print('%s  %s' % (p.default_code, p.name))
    print('   unidad=%s  lote=%s  caducidad=%s  pH=%s  analisis=%s'
          % (p.uom_id.name, p.tracking, p.amunet_expiration_text,
             p.amunet_ph_requerido, p.amunet_req_quality_control))
    for l in b.bom_line_ids.sorted('sequence'):
        print('     %-9s %-32s %8s %s' % (l.product_id.default_code,
              l.product_id.name[:32], l.product_qty, l.product_uom_id.name))
