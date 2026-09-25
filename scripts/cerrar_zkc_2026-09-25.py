"""Cierra 0926/01/ZKC (Zika Combo). Solo cambia el estado: NO produce nada.

El producto terminado ya entro el 9-sep-2026 (movimiento cerrado desde
entonces), el analisis esta aprobado y la conciliacion completa. Los dos lotes
del componente STBPR01 que bloqueaban el candado ISO ya se resolvieron: hoy
tiene uno solo.

El candado de alta manual se libera con el contexto, pero OJO con la leccion
del 23-sep: liberar el contexto NO evita que la orden produzca si su movimiento
de terminado todavia esta pendiente. Aqui es seguro porque ese movimiento ya
esta en 'done' desde el 9-sep; se verifico antes de ejecutar.

Las 355 piezas del alta manual del 7-sep SI son un duplicado, pero eso es un
tema aparte del cierre: lo va a corroborar Luis contra el fisico.
"""
mo = env['mrp.production'].search([('name','=','0926/01/ZKC')], limit=1)
assert mo, 'no existe la orden'
lote = mo.lot_producing_ids[:1]

def existencia():
    return sum(env['stock.quant'].search([
        ('lot_id','in',mo.lot_producing_ids.ids), ('location_id.usage','=','internal')]).mapped('quantity'))

# verificacion de seguridad: el movimiento de terminado ya debe estar hecho
term = env['stock.move'].search([('production_id','=',mo.id)])
pendientes = term.filtered(lambda m: m.state != 'done')
assert not pendientes, 'HAY movimientos de terminado sin hacer: cerrar produciria de nuevo'
print('verificado: el producto terminado ya entro (%s piezas, estado done)' % term.quantity)
print('ANTES : estado=%s  existencia del lote=%g pz' % (mo.state, existencia()))

mo.with_context(
    amunet_permitir_cierre_con_alta_manual=True,
    skip_consumption=True,
    skip_backorder=True,
).button_mark_done()

mo.message_post(body=(
    'Orden cerrada el 25-sep-2026. El producto terminado ya habia entrado el '
    '9-sep (368 pz a APT/Almacen Temporal PT), el analisis de calidad esta '
    'aprobado y la conciliacion completa. El cierre <b>no genero ningun '
    'ingreso nuevo</b>: solo cambio el estado de la orden.<br/><br/>'
    'Queda pendiente, como tema aparte: las 355 piezas del alta manual del '
    '7-sep-2026 (conteo fisico de Luis) estan duplicadas contra la produccion. '
    'Se pidio a Almacen PT corroborar contra el fisico antes de ajustar.'))
env.cr.commit()
print('DESPUES: estado=%s  existencia del lote=%g pz' % (mo.state, existencia()))
