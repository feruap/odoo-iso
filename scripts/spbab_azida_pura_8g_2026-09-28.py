"""SPBAB01 y SPBAB02: la azida va como reactivo puro, 8 g por litro.

Pedido por Mery el 28-sep-2026: "a las soluciones SPBAB01 y SPBAB02 suma azida de
sodio a su receta, usando 8 g por litro", y al ver lo que habia: "la A, quita la
linea de SPSAS01".

QUE HABIA, y por que no servia:

Las dos recetas ya tenian una linea de azida, pero apuntando a la SOLUCION al
20% (SPSAS01) y pidiendola en GRAMOS:

    SPSAS01  "Azida de sodio 20 %"   8.00 g

SPSAS01 se mide en LITROS. Pedirle gramos es una conversion sin sentido fisico, y
lo permitio la unidad "g" mal colgada del catalogo (la id 46, cuya jerarquia
apunta a Units en vez de a gramos; anotado como pendiente aparte). Ademas SPSAS01
nunca se ha fabricado en produccion, asi que esa linea nunca se pudo surtir: de
SPBAB01 solo hay una orden, del 13-jul, cancelada.

Si esos 8 se hubieran interpretado como 8 ml de la solucion al 20%, la receta
llevaria 1.6 g de azida y no 8.

QUE QUEDA: la linea de SPSAS01 se quita y entra la azida PURA (MPREC07) a 8 g por
litro -- 0.8% --, con su unidad propia de gramos, la correcta. Hay 100 g en
existencias, asi que se puede fabricar. El operador pesa el polvo.

Idempotente: si ya esta asi, no hace nada. Escala si la receta produjera un
volumen distinto de 1 L.
"""

PT = env['product.template'].sudo()
Bom = env['mrp.bom'].sudo()

CLAVES = ('SPBAB01', 'SPBAB02')
G_POR_LITRO = 8.0
azida = PT.search([('default_code', '=', 'MPREC07')], limit=1)
solucion = PT.search([('default_code', '=', 'SPSAS01')], limit=1)
assert azida, 'no existe MPREC07'
litro = env.ref('uom.product_uom_litre', raise_if_not_found=False)

for clave in CLAVES:
    tmpl = PT.search([('default_code', '=', clave)], limit=1)
    if not tmpl:
        print('[ojo] %s no existe en esta base' % clave); continue
    for bom in Bom.search([('product_tmpl_id', '=', tmpl.id)]):
        # Cuantos litros produce, para escalar los 8 g/L
        litros = bom.product_qty
        if litro and bom.product_uom_id != litro:
            try:
                litros = bom.product_uom_id._compute_quantity(bom.product_qty, litro)
            except Exception:
                print('   %s: la receta no esta en litros (%s), se usa la cantidad '
                      'tal cual' % (clave, bom.product_uom_id.name))
        cantidad = G_POR_LITRO * litros
        print('\n%s (receta %s, produce %g %s -> %g litros): azida %g g' % (
            clave, bom.id, bom.product_qty, bom.product_uom_id.name, litros, cantidad))

        # 1. fuera la linea de la solucion al 20%
        if solucion:
            viejas = bom.bom_line_ids.filtered(
                lambda l: l.product_id.product_tmpl_id == solucion)
            for v in viejas:
                print('   quita  %-9s %g %s' % (
                    v.product_id.default_code, v.product_qty, v.product_uom_id.name))
            if viejas:
                viejas.unlink()

        # 2. la azida pura, con SU unidad (gramos de verdad)
        linea = bom.bom_line_ids.filtered(
            lambda l: l.product_id.product_tmpl_id == azida)
        if linea:
            if (abs(linea[0].product_qty - cantidad) > 0.0001
                    or linea[0].product_uom_id != azida.uom_id):
                print('   ajusta %-9s %g %s -> %g %s' % (
                    'MPREC07', linea[0].product_qty, linea[0].product_uom_id.name,
                    cantidad, azida.uom_id.name))
                linea[0].write({'product_qty': cantidad,
                                'product_uom_id': azida.uom_id.id})
            else:
                print('   MPREC07 ya estaba con %g %s' % (cantidad, azida.uom_id.name))
        else:
            print('   agrega MPREC07   %g %s' % (cantidad, azida.uom_id.name))
            env['mrp.bom.line'].sudo().create({
                'bom_id': bom.id,
                'product_id': azida.product_variant_id.id,
                'product_qty': cantidad,
                'product_uom_id': azida.uom_id.id,
            })
        bom.message_post(body=(
            'Azida de sodio: entra el reactivo puro MPREC07 a %g g por litro '
            '(0.8%%), por indicacion de Mery del 28-sep-2026. Se quito la linea '
            'de SPSAS01 (solucion al 20%%), que estaba pedida en gramos cuando esa '
            'solucion se mide en litros, y que nunca se pudo surtir porque SPSAS01 '
            'no se ha fabricado.'
        ) % G_POR_LITRO)

print('\n=== como quedan ===')
for clave in CLAVES:
    tmpl = PT.search([('default_code', '=', clave)], limit=1)
    if not tmpl: continue
    for bom in Bom.search([('product_tmpl_id', '=', tmpl.id)]):
        print('\n%s  (produce %g %s)' % (clave, bom.product_qty, bom.product_uom_id.name))
        for l in bom.bom_line_ids.sorted(lambda x: x.product_id.default_code or ''):
            print('   %-9s %10g %s' % (
                l.product_id.default_code, l.product_qty, l.product_uom_id.name))

env.cr.commit()
