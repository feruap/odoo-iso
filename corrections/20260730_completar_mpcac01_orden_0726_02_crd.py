"""
Agrega 899 pzas de MPCAC01 (lote CAC01112402) desde AMPB/Existencias
a la orden 0726/02/CRD para completar las 3,650 pzas requeridas.

Situación original:
  - move_line id=6454: 2,751 pzas de AMP/Existencias (todo lo disponible ahí)
  - Faltan 899 pzas → se toman de AMPB/Existencias (disponibles: 3,999)
  - La demanda del move id=5938 ya es correcta: 3,650

Se agrega una segunda línea de detalle para las 899 faltantes.

Autorizado por: Karla Fernanda Palma Ramos (almacen.mp@amunet.com.mx)
Fecha: 2026-07-30
"""
import os
if os.environ.get('RUN_CORRECTION_FORCE_PROD') != 'yes-i-know-what-i-do':
    print("PROTECCIÓN: define RUN_CORRECTION_FORCE_PROD=yes-i-know-what-i-do para ejecutar en prod")
    import sys; sys.exit(0)

move = env['stock.move'].browse(5938)
lot  = env['stock.lot'].browse(1125)           # CAC01112402
loc_ampb = env['stock.location'].browse(20)    # AMPB/Existencias
loc_prod = env['stock.location'].browse(12)    # Producción
prod = move.product_id

# Verificar disponible en AMPB
quant_ampb = env['stock.quant'].search([
    ('product_id','=',prod.id), ('lot_id','=',lot.id),
    ('location_id','=',loc_ampb.id)
], limit=1)
disponible_ampb = (quant_ampb.quantity - quant_ampb.reserved_quantity) if quant_ampb else 0

print(f"Move {move.id}: demanda={move.product_uom_qty}, líneas actuales:")
for ml in move.move_line_ids:
    print(f"  ml.id={ml.id} | qty={ml.quantity} | lote={ml.lot_id.name} | loc={ml.location_id.complete_name}")
print(f"Disponible en AMPB ({lot.name}): {disponible_ampb}")

if disponible_ampb < 899:
    print(f"⚠️  No hay suficiente en AMPB (se necesitan 899, hay {disponible_ampb}). Abortando.")
    import sys; sys.exit(0)

# Crear nueva línea de detalle para 899 desde AMPB
nueva_ml = env['stock.move.line'].create({
    'move_id':           move.id,
    'product_id':        prod.id,
    'product_uom_id':    move.product_uom.id,
    'quantity':          899.0,
    'lot_id':            lot.id,
    'location_id':       loc_ampb.id,
    'location_dest_id':  loc_prod.id,
    'picking_id':        move.picking_id.id if move.picking_id else False,
})

# Reservar en el quant de AMPB
env['stock.quant']._update_reserved_quantity(prod, loc_ampb, 899.0, lot_id=lot)

env.cr.commit()
print(f"\n✅ Línea creada: ml.id={nueva_ml.id} | 899 pzas de AMPB/Existencias | lote={lot.name}")
print("Total asignado para MPCAC01 en 0726/02/CRD: 2,751 (AMP) + 899 (AMPB) = 3,650 pzas")
