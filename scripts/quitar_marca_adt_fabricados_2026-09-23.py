# El campo amunet_destino_almacen pregunta "donde entra este producto cuando se
# COMPRA". A los DM/DL/DIAM se les cargo 'adt' el 22-sep-2026 leyendo la
# clasificacion de Karla y Luis, que contestaron donde VIVE el producto. Son
# cosas distintas: esas pruebas no se compran, se fabrican internamente.
#
# El efecto secundario: la liberacion de Calidad usa esa marca para mandar el
# material a ADT, asi que un producto terminado FABRICADO se saltaba el flujo
# de APT (Temporal -> Calidad -> Temporal -> Entrega -> Existencias).
#
# Se quita la marca SOLO a los que nunca se han comprado y si tienen receta.
# Se conserva en los que de verdad son compra-venta.
T = env['product.template']
CONSERVAR = ['STHIS04', 'DMCAL01', 'PTCRS03', 'PTCRS04']   # si se compran
PREGUNTAR = ['DLBIO01', 'DLLFS01', 'DMDRO01', 'DMHBC01']   # sin definir

marcados = T.search([('amunet_va_a_distribucion', '=', True), ('active', '=', True)])
cambiados = []
for t in marcados:
    if t.default_code in CONSERVAR or t.default_code in PREGUNTAR:
        continue
    compras = env['purchase.order.line'].search_count([
        ('product_id.product_tmpl_id', '=', t.id)])
    tiene_receta = env['mrp.bom'].search_count([
        ('product_tmpl_id', '=', t.id), ('active', '=', True)])
    if compras == 0 and tiene_receta:
        t.amunet_destino_almacen = 'mp'
        cambiados.append(t.default_code)
    else:
        print('  SE DEJA %-9s compras=%s receta=%s' % (t.default_code, compras, tiene_receta))

env.cr.commit()
print('\nmarca quitada a %s productos' % len(cambiados))
print('siguen marcados: %s' % T.search_count([('amunet_va_a_distribucion', '=', True), ('active', '=', True)]))
