"""SPHMC56 -> SPHMC87 en dos recepciones y sus analisis. APLICADO EN PRODUCCION.

Lo recibido no era la hoja individual de Chikungunya (SPHMC56) sino la hoja del
combo (SPHMC87). Karla lo reporto. El 26-ago-2026 se corrigio el INVENTARIO por
ajuste (baja de SPHMC56, alta de SPHMC87 con el mismo lote), pero la recepcion y
el analisis se quedaron con el producto viejo.

Consecuencia: Almacen no podia validar AMP/IN/00352 ni AMP/IN/00391 porque el
sistema le pedia mover SPHMC56 desde Control de calidad, donde ya solo quedaban
17.6 cm. Y los analisis QC/2026/00330 y QC/2026/00340 llevaban desde el 26-ago
atorados en 'esperando recepcion'.

Cantidades: 57.6 = 60 - 2.4 y 117.6 = 120 - 2.4 (los 2.4 cm son la muestra que
toma Calidad). Verificado contra lo disponible antes de aplicar.

OJO - dos cosas que este script ensena:
  1. amunet.quality.check EXIGE `change_reason` para escribir fuera de borrador
     (control de cambios ISO 13485). Sin el campo, el write truena y la
     transaccion entera hace rollback.
  2. NO valida las recepciones: eso lo hace Almacen. El script solo corrige el
     dato; el inventario quedo identico (comprobado con fotos antes/despues).

Aplicado 24-sep-2026. Fotos en el scratchpad de la sesion.
"""

DRY = False  # aplicado 24-sep-2026

Pick = env['stock.picking']
Prod = env['product.product']
Lot  = env['stock.lot']
Chk  = env['amunet.quality.check']

nuevo = Prod.search([('default_code','=','SPHMC87')], limit=1)
viejo = Prod.search([('default_code','=','SPHMC56')], limit=1)
assert nuevo and viejo, 'faltan productos'
print('SPHMC56 uom=%s | SPHMC87 uom=%s' % (viejo.uom_id.name, nuevo.uom_id.name))
assert viejo.uom_id == nuevo.uom_id, 'unidades distintas, parar'

CASOS = [
    ('AMP/IN/00352', 729, 'HMC56072601'),
    ('AMP/IN/00391', 734, 'HMC56072602'),
]

for pick_name, check_id, lote_name in CASOS:
    print('\n===== %s / analisis %s / lote %s =====' % (pick_name, check_id, lote_name))
    p = Pick.search([('name','=',pick_name)], limit=1)
    lot_new = Lot.search([('name','=',lote_name), ('product_id','=',nuevo.id)], limit=1)
    assert lot_new, 'no existe el lote de SPHMC87'
    # disponible en Control de calidad
    disp = sum(env['stock.quant'].search([
        ('product_id','=',nuevo.id), ('lot_id','=',lot_new.id),
        ('location_id.complete_name','like','%Control de calidad%')]).mapped('quantity'))
    for m in p.move_ids:
        print('  move: %s %g %s  -> pasa a %s' % (
            m.product_id.default_code, m.product_uom_qty, m.product_uom.name, nuevo.default_code))
        print('  disponible de %s lote %s en Control de calidad: %g cm' % (
            nuevo.default_code, lote_name, disp))
        if m.product_uom_qty > disp + 0.001:
            print('  *** NO ALCANZA, revisar ***')
        if not DRY:
            m._do_unreserve()
            m.write({'product_id': nuevo.id})
            m.move_line_ids.unlink()
            m._action_assign()
            for ml in m.move_line_ids:
                ml.write({'lot_id': lot_new.id, 'quantity': m.product_uom_qty})
            if not m.move_line_ids:
                env['stock.move.line'].create({
                    'move_id': m.id, 'picking_id': p.id, 'product_id': nuevo.id,
                    'product_uom_id': m.product_uom.id, 'lot_id': lot_new.id,
                    'location_id': m.location_id.id, 'location_dest_id': m.location_dest_id.id,
                    'quantity': m.product_uom_qty})
    chk = Chk.browse(check_id)
    print('  analisis %s (%s): producto %s -> %s' % (
        chk.name, chk.state, chk.product_id.default_code, nuevo.default_code))
    if not DRY:
        chk.write({
            'product_id': nuevo.id, 'lot_id': lot_new.id,
            # el modulo exige razon de cambio fuera de borrador (control de
            # cambios ISO 13485); queda en el historial del analisis
            'change_reason': (
                'Producto corregido de SPHMC56 (Hoja Maestra Chikungunya) a '
                'SPHMC87 (Hoja Maestra Chikungunya IgG CM). Lo recibido es la '
                'hoja del combo, no la hoja individual. El inventario ya se '
                'habia corregido por ajuste el 26-ago-2026; el analisis y la '
                'recepcion se quedaron con el producto viejo y Almacen no podia '
                'validar la entrada. Confirmado por Karla (Almacen MP).'),
        })
        chk.message_post(body=(
            'Correccion 24-sep-2026: el producto era <b>SPHMC56 Hoja Maestra '
            'Chikungunya</b> y lo recibido en realidad es <b>SPHMC87 Hoja Maestra '
            'Chikungunya IgG CM</b>, la hoja del combo. El inventario ya se habia '
            'corregido por ajuste el 26-ago, pero el analisis y la recepcion se '
            'quedaron con el producto viejo, y por eso Almacen no podia validar la '
            'entrada. Confirmado por Karla (Almacen MP).'))
        p.message_post(body=(
            'Correccion 24-sep-2026: producto cambiado de SPHMC56 a SPHMC87 (hoja '
            'del combo). El inventario ya se habia corregido por ajuste el 26-ago; '
            'esta recepcion se habia quedado con el producto viejo y no se podia '
            'validar. Confirmado por Karla (Almacen MP).'))

if DRY:
    env.cr.rollback()
    print('\nSIMULACION: nada se guardo.')
else:
    env.cr.commit()
    print('\nOK: cambios guardados.')
