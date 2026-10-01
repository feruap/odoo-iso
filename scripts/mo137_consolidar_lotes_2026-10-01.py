# 0926/01/CCF (MO 137): dejar un solo lote por renglon donde se pueda.
# Los renglones se partieron solos cuando la orden crecio de 3,600 a 3,750 y
# cuando se dio de baja el BTR122502: Odoo cubre la diferencia tomando de
# otros lotes. No lo capturo nadie.
mo = env['mrp.production'].search([('name', '=', '0926/01/CCF')])
CTX = {'amunet_supply_internal': True}

def lineas(clave):
    return mo.move_raw_ids.move_line_ids.filtered(
        lambda l: l.product_id.default_code == clave)

# 1) Las 15 cajas del CAJ01042601 (sin caducidad, metidas al crecer la orden)
#    pasan al lote que Almacen surtio, que tiene 2,326 libres.
caja_destino = env['stock.lot'].search([('name', '=', 'CAJ01092601')], limit=1)
for l in lineas('MICAJ01').filtered(lambda x: x.lot_id.name == 'CAJ01042601'):
    print('MICAJ01  %s piezas: CAJ01042601 -> CAJ01092601' % l.quantity)
    l.sudo().with_context(**CTX).write({'lot_id': caja_destino.id})

# 2) Juntar en un solo renglon las lineas que ya quedaron del mismo lote.
for clave in ('MICAJ01', 'STDSC01', 'STHIS01'):
    porlote = {}
    for l in lineas(clave):
        porlote.setdefault(l.lot_id.id, []).append(l)
    for _lote, ls in porlote.items():
        if len(ls) < 2:
            continue
        total = sum(x.quantity for x in ls)
        print('%-8s juntar %s renglones del lote %s en uno de %s' % (
            clave, len(ls), ls[0].lot_id.name, total))
        ls[0].sudo().with_context(**CTX).write({'quantity': total})
        for extra in ls[1:]:
            extra.sudo().with_context(**CTX).unlink()

mo.message_post(body=(
    'Se dejo un solo lote por renglon donde se pudo. Las <b>15 cajas</b> que el '
    'sistema habia tomado del CAJ01042601 pasan al CAJ01092601, que es el que '
    'Almacen surtio, y los renglones repetidos del mismo lote quedaron juntos. '
    'Los renglones se habian partido solos: cuando la orden crecio de 3,600 a '
    '3,750 piezas, el sistema cubrio la diferencia tomando de otros lotes.<br/><br/>'
    'Siguen con mas de un lote, y por motivo distinto:<br/>'
    '- <b>Hisopos</b>: 3,600 del HIS01012601 (lo que surtio Almacen) y 150 del '
    'HIS01082601. Los dos duran mas de dos anios, asi que no corre prisa.<br/>'
    '- <b>Buffer</b>: 210 viales del BTR01032601 caducan el 30.09.28 y no hay con '
    'que cambiarlos hasta que Calidad libere los 3,526 del BTR02092603.'))
env.cr.commit()
print()
print('=== como queda ===')
for l in mo.move_raw_ids.move_line_ids.sorted(
        lambda x: (x.product_id.default_code or '', x.lot_id.name or '')):
    cad = l.lot_id.expiration_date
    print('   %-9s %-13s %-12s %9s' % (
        l.product_id.default_code, l.lot_id.name or '-',
        cad.date() if cad else 'sin caducidad', l.quantity))
