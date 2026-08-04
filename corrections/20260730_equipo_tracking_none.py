# Cambia el producto de equipo a tracking=none (serie va en Lote proveedor).
# Maneja la recepcion 1105 (VEVOR) que quedo reservada con tracking=serial.
Prod = env['product.template'].search([('default_code','=','EQUIPO-USO-INTERNO')], limit=1)
pick = env['stock.picking'].browse(1105)
try:
    if pick.exists() and pick.state not in ('done','cancel'):
        pick.do_unreserve()
        print("1105 desreservada")
except Exception as e:
    print("unreserve:", str(e)[:80])
# limpiar cualquier quant residual del producto
env['stock.quant'].sudo().search([('product_id.product_tmpl_id','=',Prod.id)]).unlink()
try:
    Prod.tracking = 'none'
    print("tracking:", Prod.tracking)
except Exception as e:
    print("ERROR tracking:", str(e)[:150])
try:
    if pick.exists() and pick.state not in ('done','cancel'):
        pick.action_assign()
        print("1105 estado:", pick.state)
except Exception as e:
    print("assign:", str(e)[:80])
env.cr.commit()
