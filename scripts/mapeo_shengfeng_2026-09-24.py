# Mapeo de claves ShengFeng -> claves internas Amunet.
#
# ShengFeng vende por MOLDE, no por producto: el K007 es un cassette liso de una
# ventana (WE-2, 70x20 mm, ventana 16x3.9 mm, HIPS/ABS - catalogo del proveedor,
# ficha 756) y lo que distingue un cartucho de otro es la impresion laser.
# Por eso la referencia de proveedor lleva molde + impresion: sin eso el PDF de
# la orden sale con claves internas que a ShengFeng no le dicen nada.
#
# Confirmado por Mery el 24-sep-2026:
#   - Salmonella typhi es impresion NUEVA (el producto pasa de comprarse hecho a
#     fabricarse en casa), por eso no aparece en ninguna factura anterior.
#   - PSA cuali y semi son las dos de hechura nacional: dos impresiones del mismo K007.
#   - HCG NET se compra armado a Tongzhou, su cassette NO pasa por ShengFeng.
#   - El K007 impreso "hCG" es el de Embarazo SSP (MPCAR65), que se fabrica aqui.
#   - "laser printing" y serigrafia son lo mismo para el caso; se deja la frase
#     textual de las facturas para que Ron la reconozca.

PROV = 'Cangzhou ShengFeng Plastic Product Co., Ltd.'
WE2 = 'K007 / Plastic cassette WE-2 (70x20mm), laser printing "%s"'

MAPEO = [
    # clave      codigo  nombre para el proveedor
    ('MPCAR65', 'K007', WE2 % 'hCG'),
    ('MPCAR01', 'K007', WE2 % 'COVINET'),
    ('MPCAR07', 'K007', WE2 % 'HbA1c'),
    ('MPCAR24', 'K007', WE2 % 'PSA'),
    ('MPCAR38', 'K007', WE2 % 'PSA s'),
    ('MPCAR45', 'K007', WE2 % 'Salmonella typhi'),
    ('MPCAR22', 'K007', WE2 % 'SIFILIS'),
    ('MPCAR06', 'K007', WE2 % 'HIV 1.2'),
    ('MPCAR20', 'K007', WE2 % 'RSV'),
    ('MPCAG01', 'K007', 'K007 / Plastic cassette WE-2 (70x20mm), white, without printing'),
    ('MPCAC03', 'K061', 'K061 / Plastic cassette Multi-2, laser printing "Dengue"'),
    ('MPCAC05', 'K061', 'K061 / Plastic cassette Multi-2, laser printing "SIFILIS+VIH"'),
    ('MPCAC07', 'K061', 'K061 / Plastic cassette Multi-2, laser printing "COVFLU" (= "COFLUNET" = "-FLU C+A+B  -COV C+T")'),
    ('STGOT01', 'DG013', 'DG013 / Transfer pipette XC-4, clear color, 10ul'),
]

# HCG NET se compra armado a Tongzhou: se retira ShengFeng de su cartucho.
QUITAR_SHENGFENG = ['MPCAR21']

S = env['product.supplierinfo']
T = env['product.template']
prov = env['res.partner'].search([('name', '=', PROV)], limit=1)
assert prov, 'No existe el proveedor %s' % PROV

print('=== CARGA ===')
for clave, codigo, nombre in MAPEO:
    t = T.search([('default_code', '=', clave)], limit=1)
    if not t:
        print('  !! %-9s NO EXISTE, se omite' % clave)
        continue
    lineas = S.search([('product_tmpl_id', '=', t.id), ('partner_id', '=', prov.id)])
    if not lineas:
        S.create({'product_tmpl_id': t.id, 'partner_id': prov.id,
                  'product_code': codigo, 'product_name': nombre})
        print('  +  %-9s %-6s creado' % (clave, codigo))
        continue
    if len(lineas) > 1:
        print('  !! %-9s tiene %s renglones de ShengFeng, se toca solo el primero'
              % (clave, len(lineas)))
    l = lineas[0]
    antes = (l.product_code or '(vacio)', l.product_name or '(vacio)')
    l.write({'product_code': codigo, 'product_name': nombre})
    print('  ~  %-9s %-6s  antes: %s / %s' % (clave, codigo, antes[0], antes[1][:40]))

print('\n=== RETIRO DE SHENGFENG (se compra armado a otro proveedor) ===')
for clave in QUITAR_SHENGFENG:
    t = T.search([('default_code', '=', clave)], limit=1)
    lineas = S.search([('product_tmpl_id', '=', t.id), ('partner_id', '=', prov.id)])
    print('  -  %-9s se borran %s renglon(es) de ShengFeng' % (clave, len(lineas)))
    lineas.unlink()
    resto = S.search([('product_tmpl_id', '=', t.id)])
    print('     queda: %s' % ', '.join(sorted(set(r.partner_id.name for r in resto))))

env.cr.commit()

print('\n=== COMO QUEDA P00226 PARA EL PROVEEDOR ===')
po = env['purchase.order'].search([('name', '=', 'P00226')], limit=1)
for lin in po.order_line:
    t = lin.product_id.product_tmpl_id
    si = S.search([('product_tmpl_id', '=', t.id), ('partner_id', '=', prov.id)], limit=1)
    cod = si.product_code if si and si.product_code else '--- SIN CODIGO ---'
    print('  %-9s %-9s %s' % (t.default_code, cod, (si.product_name or '')[:70]))
