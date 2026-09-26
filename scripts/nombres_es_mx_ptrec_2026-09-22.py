# Los reactivos PTREC tienen el nombre solo en en_US y el campo es_MX vacio.
# El sistema corre en es_MX, asi que el usuario ve el producto EN BLANCO: en el
# almacen, en la solicitud de material y en cualquier reporte. Hay existencia
# real bajo esos productos.
#
# Se copia el nombre de en_US a es_MX. Donde es_MX ya tiene algo, no se toca
# (PTREC01 dice 'Salmonella' y en_US 'Salmonela'; la buena es la de es_MX).
P = env['product.template']
prods = P.with_context(active_test=False).search([('default_code', 'like', 'PTREC')])
arreglados = 0
for p in prods:
    en = p.with_context(lang='en_US').name
    es = p.with_context(lang='es_MX').name
    if es and es.strip() and es != en:
        print('  ya tiene nombre en espanol  %-9s %s' % (p.default_code, es))
        continue
    if not en or not en.strip():
        print('  SIN NOMBRE EN NINGUN IDIOMA %-9s' % p.default_code)
        continue
    p.with_context(lang='es_MX').name = en
    arreglados += 1
    print('  copiado  %-9s -> %s' % (p.default_code, en))
env.cr.commit()
print('\nnombres copiados a es_MX: %s' % arreglados)
for p in prods:
    print('   %-9s es_MX=%r' % (p.default_code, p.with_context(lang='es_MX').name))
