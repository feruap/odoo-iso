"""
CORRECCIÓN PRODUCCIÓN — STESP01 lote ESP01072601
------------------------------------------------
Contexto:
  La solicitud SMP/26/00143 (16-jul-2026, Producción/Encartuchado) surtió
  12 esponjas del lote ESP01072601 y 42 del lote ESP01072602.
  La transferencia generada T/AMP/ENC/00136 solo registró el movimiento de
  ESP01072602 (42 piezas); el movimiento de ESP01072601 quedó marcado como
  "Completa" en el módulo SMP pero nunca decrementó el stock real.
  Resultado: el lote ESP01072601 sigue mostrando 12 piezas en AMP/Existencias
  aunque físicamente ya fueron surtidas y consumidas.

Acción:
  Ajustar AMP/Existencias → 0 para el lote ESP01072601, descontando las
  12 piezas que el sistema dejó pendientes.

Autorizado por: Karla Fernanda Palma Ramos (almacen.mp@amunet.com.mx)
Fecha: 2026-07-28
"""

loc = env['stock.location'].search([('complete_name', 'ilike', 'AMP/Existencias')], limit=1)
prod_tmpl = env['product.template'].search([('default_code', '=', 'STESP01')], limit=1)
prod = prod_tmpl.product_variant_ids[:1]
lote = env['stock.lot'].search([('name', '=', 'ESP01072601'), ('product_id', '=', prod.id)], limit=1)

if not lote:
    print("ERROR: lote ESP01072601 no encontrado")
else:
    quant = env['stock.quant'].search([
        ('product_id', '=', prod.id),
        ('lot_id', '=', lote.id),
        ('location_id', '=', loc.id),
    ], limit=1)

    qty_actual = quant.quantity if quant else 0
    print(f"Producto : {prod.display_name}")
    print(f"Lote     : {lote.name}")
    print(f"Ubicación: {loc.complete_name}")
    print(f"Qty actual en AMP/Existencias: {qty_actual}")

    if qty_actual == 0:
        print("Ya está en 0, no se requiere ajuste.")
    else:
        env['stock.quant']._update_available_quantity(
            product_id=prod,
            location_id=loc,
            quantity=-qty_actual,
            lot_id=lote,
        )
        env.cr.commit()
        print(f"\n✅ Ajuste aplicado: -{qty_actual} → saldo en 0")
        print("Motivo: SMP/26/00143 surtida/completa pero T/AMP/ENC/00136 no generó el move de stock.")
