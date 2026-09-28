"""Sube a produccion dos soluciones que solo vivian en staging: SPSAC02 y SPSCS01.

Autorizado por Mery el 28-sep-2026, al comparar el catalogo de soluciones de los
dos entornos: de las 33 a probar, 31 estaban identicas y estas dos faltaban.

    SPSAC02  Solucion de Acido Clorhidrico 0.1 M   caducidad 6 meses
             receta: MPREC37 8.3 ml + agua tridestilada, por litro
    SPSCS01  Solucion de Cloruro de Sodio 10%      caducidad 3 meses
             receta: MPREC05 100 g + agua tridestilada, por litro

Ninguna se analiza, ninguna es de uso interno (las dos se entregan a Almacen) y
ninguna ajusta pH. Los tres componentes ya existen en produccion.

DETALLE QUE NO SE ARRASTRA: en staging la linea de MPREC05 esta capturada con la
unidad "g" duplicada (la id 46, la que tiene la jerarquia mal). Aqui la receta se
crea con la unidad DEL PRODUCTO en el entorno destino, que es la "g" correcta.
Asi la migracion no propaga ese problema. Ver el pendiente de las dos unidades g.

El alta va con el contexto amunet_alta_autorizada y a nombre de Mery: el candado
de productos bloquea a los procesos automaticos a proposito.

Idempotente: si ya existen, solo completa lo que falte.
"""

PT = env['product.template'].sudo()
Bom = env['mrp.bom'].sudo()
mery = env['res.users'].sudo().search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
CATEGORIA = 'Semiprocesado / Soluciones de trabajo'

FICHAS = {
    'SPSAC02': {
        'nombre': 'Solución de Ácido Clorhídrico 0.1 M',
        'caducidad': '6 Meses',
        'receta': [('MPREC37', 8.3), ('MPATR01', 0.0496)],
    },
    'SPSCS01': {
        'nombre': 'Solución de Cloruro de Sodio 10%',
        'caducidad': '3 Meses',
        'receta': [('MPREC05', 100.0), ('MPATR01', 0.05)],
    },
    # Los dos campos de abajo van con el valor REAL que tienen en staging, no con
    # un supuesto: la primera version de este script asumio purchase_ok=False y
    # use_expiration_date=False y al correrlo en staging los cambio sin que nadie
    # lo pidiera. Una migracion copia la ficha, no la reinventa.
}
# Igual para las dos: lo que comparten todas las soluciones de trabajo.
COMUN = {
    'type': 'consu', 'is_storable': True, 'tracking': 'lot',
    'use_expiration_date': True,   # el lote lleva fecha de caducidad
    'sale_ok': False,
    'purchase_ok': True,           # se pueden comprar ya preparadas
    'amunet_req_quality_control': False,   # no se analizan al PRODUCIRLAS
    'qc_required': True,                   # si pasan por Calidad al RECIBIRLAS
                                           # (son dos banderas distintas)
    'amunet_solucion_interna': False,      # se entregan a Almacen
    'amunet_surtir_desde_mp': False,
    'amunet_resguardo_aru': 'categoria',
    'amunet_destino_almacen': 'mp',
    'amunet_ph_requerido': False,
    'amunet_req_dilution': True, 'amunet_req_aforar': True,
    'amunet_req_history_log': True, 'amunet_req_calculations': True,
    'amunet_lot_reset_monthly': True,
}

categ = env['product.category'].sudo().search([('complete_name', '=', CATEGORIA)], limit=1)
assert categ, 'no existe la categoria %s' % CATEGORIA
litro = env.ref('uom.product_uom_litre')

for clave, f in FICHAS.items():
    tmpl = PT.search([('default_code', '=', clave)], limit=1)
    vals = dict(COMUN, name=f['nombre'], default_code=clave, categ_id=categ.id,
                uom_id=litro.id, amunet_expiration_text=f['caducidad'])
    if tmpl:
        pend = {}
        for k, v in vals.items():
            actual = tmpl[k]
            if hasattr(actual, 'id'):
                actual = actual.id
            if actual != v and k != 'name':
                pend[k] = v
        if pend:
            tmpl.write(pend)
            print('[ok] %s ya existia; ajustado: %s' % (clave, sorted(pend)))
        else:
            print('[ya] %s ya existe con la configuracion correcta' % clave)
    else:
        tmpl = PT.with_user(mery).with_context(amunet_alta_autorizada=True).create(vals)
        tmpl.message_post(body=(
            'Solución dada de alta en producción por indicación de Mery '
            '(28-sep-2026). Ya existía en staging; se migra tal cual para que el '
            'catálogo de soluciones quede igual en los dos entornos.'))
        print('[ok] %s creado: %s' % (clave, f['nombre']))

    # --- la receta
    boms = Bom.search([('product_tmpl_id', '=', tmpl.id)])
    if boms:
        actual = sorted((l.product_id.default_code, round(l.product_qty, 6))
                        for l in boms[0].bom_line_ids)
        esperado = sorted((c, round(q, 6)) for c, q in f['receta'])
        print('    receta: %s' % ('ya estaba correcta' if actual == esperado
                                  else 'DISTINTA -> %s (esperada %s)' % (actual, esperado)))
        continue
    lineas = []
    falta = []
    for comp, qty in f['receta']:
        cp = PT.search([('default_code', '=', comp)], limit=1)
        if not cp:
            falta.append(comp); continue
        lineas.append((0, 0, {'product_id': cp.product_variant_id.id,
                              'product_qty': qty,
                              # la unidad del producto EN ESTE entorno
                              'product_uom_id': cp.uom_id.id}))
    if falta:
        print('    NO se crea la receta: falta(n) %s en esta base' % falta)
        continue
    bom = Bom.create({
        'product_tmpl_id': tmpl.id, 'product_qty': 1.0,
        'product_uom_id': litro.id, 'type': 'normal', 'bom_line_ids': lineas,
    })
    print('    receta creada: produce 1 L')
    for l in bom.bom_line_ids:
        print('       %-9s %g %s' % (l.product_id.default_code, l.product_qty,
                                     l.product_uom_id.name))

print('\n=== como quedan ===')
for clave in FICHAS:
    t = PT.search([('default_code', '=', clave)], limit=1)
    if not t:
        print('   %-9s NO EXISTE' % clave); continue
    print('   %-9s %-38s caducidad=%r  analiza=%s' % (
        clave, (t.name or '')[:38], t.amunet_expiration_text,
        t.amunet_req_quality_control))
    for b in Bom.search([('product_tmpl_id', '=', t.id)]):
        for l in b.bom_line_ids:
            print('      %-9s %10g %-6s (por %g %s)' % (
                l.product_id.default_code, l.product_qty, l.product_uom_id.name,
                b.product_qty, b.product_uom_id.name))

env.cr.commit()
