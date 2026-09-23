# -*- coding: utf-8 -*-
"""Alta de los 8 productos que solo existen en staging, y de sus 3 BoM.

Son productos dados de alta en staging entre nov-2025 y sep-2026 que nunca se
promovieron a produccion. Un clon de produccion los borra, asi que este script
existe para no perderlos y para poder subirlos cuando se decida.

  docker cp alta_pendientes_staging.py odoo-staging:/tmp/x.py
  docker exec odoo-staging bash -c 'odoo shell -c /etc/odoo/odoo.conf \
    -d Amunet_testing --no-http --db_host $HOST --db_port $PORT \
    --db_user $USER --db_password $PASSWORD < /tmp/x.py'

Idempotente: la segunda corrida no duplica nada.

NO incluye PTCRS01 "Matraz 5 L" a proposito: Karla confirmo el 21-sep-2026 que
nunca existio fisicamente y que estaba bien sacarlo del catalogo.

DOS COSAS QUE HAY QUE REVISAR antes de subir esto a produccion (se recrean tal
como estan en staging, sin corregirlas, porque la decision no es tecnica):
  - PTCRS02 "Lampara de alcohol" esta en la categoria Producto terminado /
    Cristaleria y marcada VENDIBLE, pero su almacen es Materia prima. O es de
    venta y vive en Distribucion, o es insumo y no deberia ser vendible.
  - MPREC98 EDTA y MPANT69 (anticuerpo) son materia prima y estan marcados
    VENDIBLES. Revisar si de verdad se venden.
"""
P = env['product.product'].sudo()
T = env['product.template'].sudo().with_context(amunet_alta_autorizada=True)
B = env['mrp.bom'].sudo()
C = env['product.category'].sudo()
U = env['uom.uom'].sudo()

DESC_HM = ('Prueba rápida para la detección de ADN amplificado de %s '
           'marcado con FITC.')

# clave, nombre, categoria, uom, caduca, compra, venta, almacen, descripcion
PRODUCTOS = [
    ('SPHMT03', 'Hoja Maestra VPH', 'Semiprocesado / Hoja maestra', 'cm',
     True, True, False, 'mp', DESC_HM % 'Virus del Papiloma Humano (VPH)'),
    ('SPHMT04', 'Hoja Maestra Pylorinet', 'Semiprocesado / Hoja maestra', 'cm',
     True, True, False, 'mp', DESC_HM % 'Helicobacter pylori (Pylorinet)'),
    ('SPHMT05', 'Hoja Maestra TB-DxNet', 'Semiprocesado / Hoja maestra', 'cm',
     True, True, False, 'mp', DESC_HM % 'Mycobacterium tuberculosis (TB-DxNet)'),
    ('PTCRS02', 'Lámpara de alcohol', 'Producto terminado / Cristalería', 'Units',
     False, True, True, 'mp', ''),
    ('PTCRS03', 'Probeta 1 L', 'Distribucion', 'Units',
     False, True, True, 'adt', ''),
    ('PTCRS04', 'Probeta 250 mL', 'Distribucion', 'Units',
     False, True, True, 'adt', ''),
    ('MPREC98', 'EDTA', 'Materia prima / Reactivo', 'g',
     False, True, True, 'mp', ''),
    ('MPANT69', 'Anticuerpo control de detección', 'Materia prima / Anticuerpo', 'mg',
     True, True, True, 'mp', ''),
]

# Las 3 hojas maestras llevan la misma receta: 1 tarjeta de soporte y 1
# almohadilla absorbente A11, y producen los 30 cm de una hoja.
BOMS = [('SPHMT03', 30.0), ('SPHMT04', 30.0), ('SPHMT05', 30.0)]
COMPONENTES_HM = [('MPTS01', 1.0), ('SPALMA11', 1.0)]

creados = omitidos = 0
rechazados = []
for cod, nombre, categ, uom, caduca, compra, venta, almacen, desc in PRODUCTOS:
    if T.search([('default_code', '=', cod)], limit=1):
        print('   %-9s ya existe, se omite' % cod)
        omitidos += 1
        continue
    cat = C.search([('complete_name', '=', categ)], limit=1)
    assert cat, 'falta la categoria %s' % categ
    u = U.search([('name', '=', uom)], limit=1)
    assert u, 'falta la unidad %s' % uom
    vals = {
        'default_code': cod, 'name': nombre, 'categ_id': cat.id,
        'uom_id': u.id, 'type': 'consu', 'is_storable': True,
        'tracking': 'lot', 'purchase_ok': compra, 'sale_ok': venta,
    }
    if 'use_expiration_date' in T._fields:
        vals['use_expiration_date'] = caduca
    if 'amunet_destino_almacen' in T._fields:
        vals['amunet_destino_almacen'] = almacen
    if desc:
        vals['description'] = '<p>%s</p>' % desc
    # Cada producto en su savepoint: uno que el sistema rechace no debe tumbar
    # a los demas. Paso con PTCRS02, que en staging quedo VENDIBLE sin BoM en
    # 'Producto terminado' -- una combinacion que amunet_distribucion ya no
    # permite. Se creo en jun-2026, antes de que existiera ese candado.
    try:
        with env.cr.savepoint():
            t = T.create(vals)
            # el nombre es traducible: si no se escribe tambien en es_MX el
            # usuario sigue viendo el valor en ingles
            t.with_context(lang='es_MX').write({'name': nombre})
    except Exception as e:
        rechazados.append((cod, str(e).strip().split('\n')[0]))
        print('   %-9s RECHAZADO por el sistema:' % cod)
        print('             %s' % str(e).strip().split('\n')[0][:150])
        continue
    creados += 1
    print('   %-9s CREADO  %-34s %-30s %s' % (cod, nombre[:34], categ[:30], uom))

boms_creados = 0
for cod, qty in BOMS:
    prod = P.search([('default_code', '=', cod)], limit=1)
    if not prod:
        print('   BoM %-9s sin producto, se omite' % cod)
        continue
    if B.search([('product_tmpl_id', '=', prod.product_tmpl_id.id)], limit=1):
        print('   BoM %-9s ya existe, se omite' % cod)
        continue
    lineas = []
    for ccod, cqty in COMPONENTES_HM:
        comp = P.search([('default_code', '=', ccod)], limit=1)
        assert comp, 'falta el componente %s' % ccod
        lineas.append((0, 0, {'product_id': comp.id, 'product_qty': cqty,
                              'product_uom_id': comp.uom_id.id}))
    B.create({
        'product_tmpl_id': prod.product_tmpl_id.id,
        'product_qty': qty, 'product_uom_id': prod.uom_id.id,
        'type': 'normal',
        'bom_line_ids': lineas,
    })
    boms_creados += 1
    print('   BoM %-9s produce %g %s <- %s' % (
        cod, qty, prod.uom_id.name, ', '.join(c for c, _q in COMPONENTES_HM)))

env.flush_all()
env.cr.commit()
print('PRODUCTOS creados: %d   ya existian: %d   BoM creados: %d   rechazados: %d' % (
    creados, omitidos, boms_creados, len(rechazados)))
if rechazados:
    print('')
    print('PENDIENTES DE DECISION -- el sistema los rechazo y hay que resolverlos')
    print('a mano, no forzarlos:')
    for cod, msg in rechazados:
        print('  - %s: %s' % (cod, msg[:160]))
