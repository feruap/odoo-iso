"""PTBWP01 y PTESP01: les da su presentacion para que se puedan planear.

Pedido por Mery el 30-sep-2026: estaba armando una orden de bolsas y el plan de empaque la
freno con "No hay presentaciones autorizadas para [PTBWP01] Paquete con 10 bolsas
Whirl-Pak esterilizadas".

LA CAUSA: los dos productos tenian CERO presentaciones, y _authorized_presentations() del
plan de empaque exige al menos una autorizada y activa antes de dejar planear. No es un
bug: es configuracion que faltaba. Los 82 productos que si planean tienen entre una y tres
cada uno, 153 en total.

POR QUE package_qty = 1 Y NO 10. El producto YA ES el paquete de diez: PTBWP01 se llama
"Paquete con 10 bolsas" y en ADT/Stock hay 2 unidades, que son 2 paquetes, igual que las 2
que publica la tienda. Con package_qty = 10 el sistema entenderia diez PAQUETES por
presentacion -- cien bolsas- y el plan saldria diez veces mas grande.

El patron de la casa confirma la lectura al reves: PTREC01 tiene "Medio de Cultivo
Salmonella 10 piezas" con qty 10 porque alli la unidad del producto es la PIEZA suelta, no
el paquete.

ETIQUETA SI, MANUAL NO. Los demas productos con presentacion son pruebas rapidas y llevan
las dos en si. Una bolsa esteril y un kit de esponjas para toma de muestra no llevan
instructivo de uso, asi que manual_required queda en False. La etiqueta si: es material
controlado y se rotula.

Probado en staging antes: con la presentacion puesta, _authorized_presentations() devuelve
la presentacion y el plan deja pasar.

Idempotente.
"""
Pres = env['amunet.packaging.presentation'].sudo()

CASOS = [
    ('PTBWP01', 'Paquete con 10 bolsas'),
    ('PTESP01', 'Kit de 10 esponjas'),
]

for clave, nombre in CASOS:
    t = env['product.template'].sudo().search([('default_code', '=', clave)], limit=1)
    if not t:
        print('[ojo] no existe %s' % clave); continue
    ya = Pres.with_context(active_test=False).search([('product_tmpl_id', '=', t.id)])
    if ya:
        print('[ya] %-9s tiene %d presentacion(es): %s' % (
            clave, len(ya), ', '.join('%s (qty %s, autorizada=%s)' % (
                x.name, x.package_qty, x.is_authorized) for x in ya)))
        # si existe pero sin autorizar, el candado sigue cerrado
        sin_aut = ya.filtered(lambda x: not (x.is_authorized and x.active))
        if sin_aut and not ya.filtered(lambda x: x.is_authorized and x.active):
            sin_aut[0].write({'is_authorized': True, 'active': True})
            print('       [ok] se autorizo la existente, el candado ya deja pasar')
        continue
    pr = Pres.create({
        'product_tmpl_id': t.id,
        'name': nombre,
        'package_qty': 1,
        'is_authorized': True,
        'authorization_source': 'manual',
        'label_required': True,
        'manual_required': False,
    })
    print('[ok] %-9s presentacion %s: "%s"  qty %s  etiqueta=si  manual=no' % (
        clave, pr.id, pr.name, pr.package_qty))

print('\n=== el candado deja planear los dos? ===')
Plan = env['amunet.packaging.plan'].sudo()
for clave, _n in CASOS:
    t = env['product.template'].sudo().search([('default_code', '=', clave)], limit=1)
    p = env['product.product'].sudo().search([('product_tmpl_id', '=', t.id)], limit=1)
    tmp = Plan.new({'product_tmpl_id': t.id, 'product_id': p.id})
    try:
        ps = tmp._authorized_presentations()
        print('   %-9s SI: %s' % (clave, ', '.join('%s (qty %s)' % (x.name, x.package_qty) for x in ps)))
    except Exception as e:
        print('   %-9s SIGUE BLOQUEADO: %s' % (clave, str(e)[:90]))
env.cr.commit()
