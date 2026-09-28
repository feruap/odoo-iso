# -*- coding: utf-8 -*-
"""Meter los conjugados en la receta de las 15 hojas que se laminan aqui.

EL PROBLEMA. La receta de una hoja maestra traia membrana, tarjeta y
almohadillas, pero NO el conjugado. El conjugado se imprime en el paso 10 de
la ruta, y ese paso es solo texto: no descuenta nada. Resultado: al fabricar
una hoja el conjugado no salia del inventario y, peor, no quedaba ligado al
lote de la hoja. Para Cofepris eso es justo lo que tiene que quedar asentado.

LA CANTIDAD. La receta produce 30 cm de hoja (product_qty=30, uom=cm), asi
que el consumo sale directo: ul/cm x 30 cm. Se captura en ul, que es como lo
piensa el operador; ul es submultiplo de ml, la unidad del producto.

DATOS. Archivo "Conjugado por hoja maestra" que devolvio Mery el 28-sep-2026
(version 22:31, la corregida).

TRES HOJAS SIN CONJUGADO EXTRA DE CONTROL. SPHMC15, SPHMC19 y SPHMC38 si
llevan linea de control -se imprime en la membrana-, pero no una segunda
almohadilla con su propio conjugado: el de prueba sirve para las dos lineas.
Por eso se les quita SPALMA03 de la receta Y del texto del laminado. Dejar el
texto sin quitar la almohadilla manda al operador a buscar un material que ya
no le surtieron.

Idempotente.
"""
CM_POR_HOJA = 30.0

# hoja: (conjugado_control, ul_cm_control, [(conjugado_prueba, ul_cm), ...])
PLAN = {
    'SPHMC01': ('SPCDE21', 2, [('SPCDE08', 10)]),
    'SPHMC18': ('SPCDE12', 3, [('SPCDE09', 10)]),
    'SPHMC19': (None, None, [('SPCDE10', 30)]),
    'SPHMC15': (None, None, [('SPCDE01', 10), ('SPCDE02', 10)]),
    'SPHMC24': ('SPCDE21', 2, [('SPCDE14', 10)]),
    'SPHMC38': (None, None, [('SPCDE14', 30)]),
    'SPHMC20': ('SPCDE21', 2, [('SPCDE17', 14)]),
    'SPHMC22': ('SPCDE29', 10, [('SPCDE22', 10)]),
    'SPHMC23': ('SPCDE21', 2, [('SPCDE26', 10)]),
    'SPHMC09': ('SPCDE21', 2, [('SPCDE18', 24)]),
    'SPHMT01': ('SPCDE12', 3, [('SPCDE03', 10)]),
    'SPHMC07': ('SPCDE12', 3, [('SPCDE13', 10)]),
    'SPHMC45': ('SPCDE21', 2, [('SPCDE24', 10)]),
    'SPHMC37': ('SPCDE21', 2, [('SPCDE19', 14)]),
    'SPHMC52': ('SPCDE21', 2, [('SPCDE19', 30)]),
}

SIN_A3 = ('SPHMC15', 'SPHMC19', 'SPHMC38')

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

ul = env['uom.uom'].search([('name', '=', 'µl')], limit=1)
assert ul, 'No existe la unidad ul'
a3 = env['product.product'].search([('default_code', '=', 'SPALMA03')], limit=1)
assert a3, 'No existe SPALMA03'


def prod(clave):
    p = env['product.product'].search([('default_code', '=', clave)], limit=1)
    assert p, 'No existe %s' % clave
    return p


def bom_de(clave):
    h = prod(clave)
    b = env['mrp.bom'].search([('product_tmpl_id', '=', h.product_tmpl_id.id)])
    assert len(b) == 1, '%s tiene %d recetas' % (clave, len(b))
    assert b.product_qty == CM_POR_HOJA, '%s produce %s, no %s cm' % (
        clave, b.product_qty, CM_POR_HOJA)
    return b


quitadas, agregadas, rutas = [], [], []

# --- 1. quitar la almohadilla de control de las tres que no la llevan -------
for clave in SIN_A3:
    b = bom_de(clave)
    l = b.bom_line_ids.filtered(lambda x: x.product_id == a3)
    if l:
        l.unlink()
        quitadas.append(clave)
    for op in b.operation_ids:
        nuevo = op.name.replace('conjugado control SPALMA03, ', '')
        if nuevo != op.name:
            op.name = nuevo
            rutas.append((clave, op.sequence, nuevo))

# --- 2. meter los conjugados ----------------------------------------------
for clave, (ctrl, ul_ctrl, pruebas) in PLAN.items():
    b = bom_de(clave)
    lineas = list(pruebas) + ([(ctrl, ul_ctrl)] if ctrl else [])
    for conj, ul_cm in lineas:
        p = prod(conj)
        cantidad = ul_cm * CM_POR_HOJA
        ya = b.bom_line_ids.filtered(lambda x: x.product_id == p)
        if ya:
            if abs(ya[0].product_qty - cantidad) > 1e-6 or ya[0].product_uom_id != ul:
                ya[0].write({'product_qty': cantidad, 'product_uom_id': ul.id})
                agregadas.append((clave, conj, cantidad, 'ajustada'))
            continue
        env['mrp.bom.line'].create({
            'bom_id': b.id, 'product_id': p.id,
            'product_qty': cantidad, 'product_uom_id': ul.id,
        })
        agregadas.append((clave, conj, cantidad, 'nueva'))

    # el paso 10 decia 10 ul/cm en todas; ahora dice el volumen real y cual
    texto = ' + '.join('%s a %s ul/cm' % (c, v) for c, v in pruebas)
    for op in b.operation_ids.filtered(lambda o: o.sequence == 10):
        base = op.name.split(' - ', 1)
        cola = (' - ' + base[1]) if len(base) > 1 else ''
        pad = 'SPALMA02' if 'SPALMA02' in op.name else 'SPALMA01'
        nuevo = 'Impresion de conjugado %s en %s%s' % (texto, pad, cola)
        if nuevo != op.name:
            op.name = nuevo
            rutas.append((clave, 10, nuevo))

env.cr.commit()

print('=' * 92)
print('ALMOHADILLA A3 QUITADA: %s' % (', '.join(quitadas) or 'ninguna'))
print('-' * 92)
for clave, conj, qty, estado in agregadas:
    print('  %-9s %-9s %7.0f ul  (%s)' % (clave, conj, qty, estado))
print('-' * 92)
for clave, seq, txt in rutas:
    print('  ruta %-9s paso %-3s %s' % (clave, seq, txt[:70]))
print('=' * 92)
