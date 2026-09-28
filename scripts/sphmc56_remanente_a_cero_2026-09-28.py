"""SPHMC56: las 17.6 cm que quedaron en cuarentena son doble conteo. A cero.

Autorizado por Mery el 28-sep-2026.

EL CASO, reconstruido del historial del lote HMC56072602:

    29-jul  SPHMC56  se reciben 120 cm            (AMP/IN/00159)
    26-ago  SPHMC87  +120 por ajuste  <-- se reclasifica a la clave correcta
    26-ago  SPHMC56  -120 por ajuste
    02-sep  SPHMC56  20 cm regresan a cuarentena  (AMP/QC/00405)
    03-sep  SPHMC56  2.4 cm a Desechos (la muestra de Calidad)
    22-sep  SPHMC56  +20 por ajuste
    25-sep  SPHMC87  117.6 cm a Existencias       (AMP/IN/00391)

Lo recibido no era la hoja individual de Chikungunya (SPHMC56) sino la del combo
(SPHMC87). El material fisico ya esta completo bajo la clave correcta:
117.6 en existencias + 2.4 de muestra = 120 cm. Pero SPHMC56 se quedo con 17.6 cm
VIVAS en Control de calidad -- los 20 que regresaron el 2-sep menos los 2.4 de la
muestra -- y esas son las MISMAS piezas ya contadas como SPHMC87.

O sea: 17.6 cm contadas dos veces. No hay material que analizar ahi.

Por eso el script de Calidad del 28-sep les creo el analisis QC/2026/00509: vio
material en cuarentena sin analizar. Ese analisis queda sin razon de ser; su
cancelacion la decide Calidad, no este script.

El analisis del material real (QC/2026/00340, SPHMC87) esta autorizado y cerrado
desde julio y NO SE TOCA.

QUE HACE: baja a cero las 17.6 cm de SPHMC56 en Control de calidad, por ajuste de
inventario con la ORM, y deja la explicacion en el producto y en el lote.
NO toca SPHMC87, ni el analisis viejo, ni ningun otro producto.

Idempotente: si ya esta en cero, no hace nada. Guarda: si SPHMC87 no tiene sus
120 cm, NO ajusta -- eso significaria que el material bueno no esta contado y las
17.6 podrian ser reales.
"""

Quant = env['stock.quant'].sudo()
Prod = env['product.product'].sudo()
Lot = env['stock.lot'].sudo()

CLAVE_MALA, CLAVE_BUENA, LOTE = 'SPHMC56', 'SPHMC87', 'HMC56072602'
# El material bueno del MISMO lote tiene que estar contado: 117.6 cm es lo que
# queda de los 120 recibidos despues de la muestra de 2.4 que tomo Calidad. Se
# usa como minimo y no como igualdad porque segun el momento esas 117.6 pueden
# estar en existencias, en cuarentena, o repartidas.
MINIMO_BUENO = 117.6

malo = Prod.search([('default_code', '=', CLAVE_MALA)], limit=1)
bueno = Prod.search([('default_code', '=', CLAVE_BUENA)], limit=1)
assert malo and bueno, 'no existe alguno de los dos productos'
lote_malo = Lot.search([('name', '=', LOTE), ('product_id', '=', malo.id)], limit=1)
if not lote_malo:
    print('no existe el lote %s de %s en esta base: nada que hacer' % (LOTE, CLAVE_MALA))
else:
    def foto(titulo):
        print('\n-- %s --' % titulo)
        for clave, p in ((CLAVE_MALA, malo), (CLAVE_BUENA, bueno)):
            qs = Quant.search([('product_id', '=', p.id),
                               ('location_id.usage', '=', 'internal')])
            tot = sum(qs.mapped('quantity'))
            print('   %-9s total interno %g cm' % (clave, tot))
            for q in qs.filtered(lambda x: x.quantity):
                print('      %-34s %g cm  lote %s' % (
                    q.location_id.complete_name[:34], q.quantity,
                    q.lot_id.name or '-'))
        return

    foto('ANTES')

    # Guarda: el material bueno tiene que estar contado BAJO ESTE MISMO LOTE, si
    # no las 17.6 podrian ser material real y no un duplicado. Se mira el lote y
    # no el total del producto: SPHMC87 tiene otros lotes que no vienen al caso.
    lote_bueno = Lot.search([('name', '=', LOTE), ('product_id', '=', bueno.id)], limit=1)
    del_lote = sum(Quant.search([
        ('product_id', '=', bueno.id), ('lot_id', '=', lote_bueno.id),
        ('location_id.usage', '=', 'internal')]).mapped('quantity')) if lote_bueno else 0.0
    if del_lote < MINIMO_BUENO:
        print('\nNO SE AJUSTA: el lote %s de %s tiene %g cm y deberia tener al '
              'menos %g. Si el material bueno no esta contado, las %g cm de %s '
              'podrian ser reales. Revisar antes de tocar nada.' % (
                  LOTE, CLAVE_BUENA, del_lote, MINIMO_BUENO,
                  sum(Quant.search([('product_id', '=', malo.id),
                                    ('lot_id', '=', lote_malo.id),
                                    ('location_id.usage', '=', 'internal')]).mapped('quantity')),
                  CLAVE_MALA))
    else:
        quants = Quant.search([
            ('product_id', '=', malo.id), ('lot_id', '=', lote_malo.id),
            ('location_id.usage', '=', 'internal')]).filtered(lambda q: q.quantity)
        if not quants:
            print('\n%s lote %s ya esta en cero: nada que ajustar' % (CLAVE_MALA, LOTE))
        else:
            bajado = 0.0
            for q in quants:
                print('\n   ajustando %-9s %-32s %g -> 0' % (
                    CLAVE_MALA, q.location_id.complete_name[:32], q.quantity))
                bajado += q.quantity
                q.with_context(inventory_mode=True).write({
                    'inventory_quantity': 0,
                    'inventory_diff_quantity': -q.quantity,
                })
                q.with_context(inventory_mode=True).action_apply_inventory()
            MOTIVO = (
                'Ajuste de inventario autorizado por Mery el 28-sep-2026: se '
                'bajan %g cm del lote %s en Control de calidad porque estaban '
                'contadas dos veces. Lo recibido no era esta hoja (SPHMC56) sino '
                'la del combo (SPHMC87), y el material fisico ya esta completo '
                'bajo esa clave: 117.6 cm en existencias mas 2.4 cm de muestra. '
                'Las 17.6 cm de aqui son los 20 cm que regresaron a cuarentena el '
                '2-sep menos la muestra, o sea las mismas piezas. El analisis del '
                'material real (QC/2026/00340) esta autorizado desde julio y no se '
                'toca.'
            ) % (bajado, LOTE)
            malo.product_tmpl_id.message_post(body=MOTIVO)
            lote_malo.message_post(body=MOTIVO)
            print('\n   bajadas %g cm y explicacion registrada en el producto y el lote' % bajado)

    foto('DESPUES')

env.cr.commit()
print('\nlisto.')
