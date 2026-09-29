"""Tres almacenamientos que Karla confirmo con conteo fisico.

Autorizado por Mery el 29-sep-2026, con el conteo de Karla del mismo dia.

CASO 1 -- SPHMC75 y SPHMC76 (hojas maestras)
Habia DOS documentos para el mismo material, hechos con un dia de diferencia y en
unidades distintas:

    AMP/STOR/00094  (5-ago)   30 de cada una   <- capturado como si fueran HOJAS
    AMP/STOR/00098  (6-ago)  900 de cada una   <- en cm, la unidad real del producto

Las hojas se miden en CENTIMETROS y hay 900 cm en cuarentena de cada una, o sea las
30 hojas de 30 cm que conto Karla. El documento correcto es el de 900; el de 30
pediria 30 cm, que es una sola hoja.

Karla: "Confirmo que tengo fisicamente 30 hojas de cada una (900 cm), no 31. Procede
a validar el AMP/STOR/00098 y cancelar el AMP/STOR/00094."

CASO 2 -- STCPL04 (Control Positivo VPH NET)
AMP/STOR/00100 pide 100 pzas y en cuarentena hay 27, del lote CPL04092603 -- el que
se renombro ayer. Karla: "confirmo que tengo fisicamente 27 pzas en Control de
Calidad. Procede a hacer el movimiento nuevo por 27 y cancelar el documento de 100."

QUE HACE: valida el de 900, cancela el de 30, y para STCPL04 ajusta el documento a
las 27 reales y lo valida, en vez de crear uno nuevo -- asi no se pierde el hilo con
el documento que Almacen ya tiene a la vista.

Idempotente: si ya estan validados o cancelados, no hace nada.
"""

Pick = env['stock.picking'].sudo()

def validar(nombre, esperado=None):
    p = Pick.search([('name', '=', nombre)], limit=1)
    if not p:
        print('   [ojo] %s no existe' % nombre); return
    if p.state == 'done':
        print('   [ya] %s ya esta validado' % nombre); return
    if p.state == 'cancel':
        print('   [ojo] %s esta CANCELADO, no se valida' % nombre); return
    for m in p.move_ids:
        print('      %-9s pide %g %s' % (m.product_id.default_code,
                                         m.product_uom_qty, m.product_uom.name))
        if esperado is not None and abs(m.product_uom_qty - esperado) > 0.001:
            m.write({'product_uom_qty': esperado})
            print('         ajustado a %g (lo que conto Karla)' % esperado)
    p.action_assign()
    faltan = p.move_ids.filtered(lambda m: m.quantity < m.product_uom_qty - 0.001)
    if faltan:
        for m in faltan:
            print('      NO se puede validar: %s reservo %g de %g' % (
                m.product_id.default_code, m.quantity, m.product_uom_qty))
        return
    p.button_validate()
    p.invalidate_recordset()
    print('   [ok] %s validado (estado %s)' % (nombre, p.state))
    p.message_post(body=(
        'Validado el 29-sep-2026 con el conteo fisico que confirmo Karla y la '
        'autorizacion de Mery.'))

def cancelar(nombre, motivo):
    p = Pick.search([('name', '=', nombre)], limit=1)
    if not p:
        print('   [ojo] %s no existe' % nombre); return
    if p.state == 'cancel':
        print('   [ya] %s ya esta cancelado' % nombre); return
    if p.state == 'done':
        print('   [OJO] %s ya esta VALIDADO: no se cancela' % nombre); return
    p.action_cancel()
    p.invalidate_recordset()
    print('   [ok] %s cancelado (estado %s)' % (nombre, p.state))
    p.message_post(body=motivo)

print('-- CASO 1: las hojas SPHMC75 y SPHMC76 --')
print('   valido el de 900 cm (la unidad real del producto):')
validar('AMP/STOR/00098')
print('   cancelo el duplicado de 30:')
cancelar('AMP/STOR/00094', (
    'Cancelado el 29-sep-2026, autorizado por Mery con el conteo de Karla.'
    '<br/><br/>Era un duplicado de AMP/STOR/00098: el mismo material capturado un '
    'dia antes y en la unidad equivocada. Las hojas se miden en CENTIMETROS, y este '
    'documento pedia 30, que es una sola hoja. El correcto es el de 900 cm -- las 30 '
    'hojas de 30 cm que Karla conto fisicamente --, y ese quedo validado.'))

print('\n-- CASO 2: STCPL04, de 100 a las 27 reales --')
validar('AMP/STOR/00100', esperado=27.0)

print('\n=== como quedan ===')
for n in ('AMP/STOR/00094', 'AMP/STOR/00098', 'AMP/STOR/00100'):
    p = Pick.search([('name', '=', n)], limit=1)
    if not p:
        continue
    print('   %-15s %s   %s' % (n, p.state, ', '.join(
        '%s %g %s' % (m.product_id.default_code, m.quantity or m.product_uom_qty,
                      m.product_uom.name) for m in p.move_ids)))
print('\n   en cuarentena despues:')
for clave in ('SPHMC75', 'SPHMC76', 'STCPL04'):
    pp = env['product.product'].sudo().search([('default_code', '=', clave)], limit=1)
    q = sum(env['stock.quant'].sudo().search([
        ('product_id', '=', pp.id),
        ('location_id.complete_name', 'like', '%Control de calidad%')]).mapped('quantity'))
    ex = sum(env['stock.quant'].sudo().search([
        ('product_id', '=', pp.id),
        ('location_id.complete_name', '=', 'AMP/Existencias')]).mapped('quantity'))
    print('      %-9s cuarentena %8g   existencias %8g' % (clave, q, ex))
env.cr.commit()
