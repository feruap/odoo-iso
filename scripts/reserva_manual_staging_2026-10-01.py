# STAGING: las ordenes de manufactura dejan de apartar material al confirmarse.
# Lo aparta Almacen cuando aprieta "Comprobar disponibilidad", que es cuando de
# verdad va a surtir. (Mery, 1-oct-2026)
#
# Por que: una orden confirmada para dentro de dos semanas competia por el
# material con la que se fabrica hoy. En produccion, 1026/01/VID y 1026/01/CRD
# -- que arrancan el 2 y el 5 de octubre y no tienen un solo renglon surtido --
# tenian apartadas 4,408 bolsas y 3,600 viales de buffer. Y soltarlo a mano no
# sirve: en cuanto entra existencia, la orden vuelve a apartarla sola.
#
# Probado antes de aplicar: con manual, una orden sin surtir NO vuelve a
# apartar cuando entra material, y al apretar el boton Almacen sigue viendo su
# lote prellenado. No se pierde el prellenado, solo pasa a ser a demanda.
#
# NO se toca by_date porque exigiria encender "Procurement: run scheduler",
# que esta apagado y ademas dispara las reglas de reabastecimiento.
tipos = env['stock.picking.type'].search([('code', '=', 'mrp_operation')])
for t in tipos:
    print('%-34s %s -> manual' % (
        t.warehouse_id.name or t.name, t.reservation_method))
tipos.write({'reservation_method': 'manual'})
env.cr.commit()
print()
for t in env['stock.picking.type'].search([('code', '=', 'mrp_operation')]):
    print('   %-34s %s' % (t.warehouse_id.name or t.name, t.reservation_method))
