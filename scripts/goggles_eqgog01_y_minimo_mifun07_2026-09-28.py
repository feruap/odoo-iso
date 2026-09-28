# -*- coding: utf-8 -*-
"""Dos cosas que autorizo Mery el 28-sep-2026, corre en staging y en produccion.

1. MIFUN07 (Funda para caja PCR VPH): el minimo de Fabrica baja de 50 a 40.
   Lo propuso Karla: Fabrica tiene 180 pzas y Burgos 292, el minimo casi no se
   activa. El maximo se queda en 50, asi que cuando baje de 40 repone a 50.

2. Alta de EQGOG01 (Goggles de seguridad UVEX, Honeywell), clave asignada por
   Documentacion. Ficha preparada por Luis (Almacen 2), identica a sus hermanos
   EQVOR01 / EQMIC01 / EQINC01, con UNA diferencia que indico Mery: este vive en
   DISTRIBUCION (ADT), no en materia prima como ellos.

   El precio de venta lo definen Luis y Fernando: queda en 0.
   La existencia inicial es 0 a proposito; el material no se sube todavia.

Idempotente: busca por clave y solo escribe lo que falta.
"""
PT = env['product.template']
OP = env['stock.warehouse.orderpoint']

# ---------------------------------------------------------------- 1. MIFUN07
fun = PT.search([('default_code', '=', 'MIFUN07')], limit=1)
if not fun:
    print('[ojo] MIFUN07 no existe en esta base, no se toca el minimo')
else:
    ops = OP.search([('product_id', 'in', fun.product_variant_ids.ids)])
    for op in ops:
        alm = op.warehouse_id.code
        if op.product_min_qty == 40:
            print('[ya] %s (%s) minimo ya esta en 40' % (op.name, alm))
            continue
        antes = op.product_min_qty
        op.write({'product_min_qty': 40})
        print('[ok] %s (%s) minimo %s -> 40 (maximo se queda en %s)' % (
            op.name, alm, antes, op.product_max_qty))
    if not ops:
        print('[ojo] MIFUN07 no tiene regla de reabastecimiento en esta base')

# ---------------------------------------------------------------- 2. EQGOG01
CLAVE = 'EQGOG01'
gog = PT.search([('default_code', '=', CLAVE)], limit=1)
hermano = PT.search([('default_code', '=', 'EQVOR01')], limit=1)
if not hermano:
    print('[ojo] no esta EQVOR01 para copiarle la configuracion; se omite el alta')
else:
    vals = {
        'name': 'Goggles de seguridad UVEX (Honeywell)',
        'default_code': CLAVE,
        'categ_id': hermano.categ_id.id,
        'type': hermano.type,
        'is_storable': True,
        'tracking': 'lot',
        'use_expiration_date': False,
        'uom_id': hermano.uom_id.id,
        'sale_ok': True,
        'purchase_ok': True,
        # la diferencia con sus hermanos: este se compra para VENDER
        'amunet_destino_almacen': 'adt',
        'amunet_requires_quarantine': hermano.amunet_requires_quarantine,
        'amunet_req_quality_control': hermano.amunet_req_quality_control,
        'nombre_etiqueta': 'Goggles UVEX',
    }
    if gog:
        pend = {}
        for k, v in vals.items():
            actual = gog[k]
            if hasattr(actual, 'id'):
                actual = actual.id
            if actual != v:
                pend[k] = v
        if pend:
            gog.write(pend)
            print('[ok] %s ya existia; se ajusto: %s' % (CLAVE, list(pend)))
        else:
            print('[ya] %s ya existe con la configuracion correcta' % CLAVE)
    else:
        # El alta de un producto es un acto autorizado: va con el contexto
        # explicito y a nombre de quien la autoriza (Mery).
        mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
        gog = PT.with_user(mery).with_context(amunet_alta_autorizada=True).create(vals)
        print('[ok] %s creado: %s' % (CLAVE, gog.name))

    # El precio de venta en 0 porque lo definen Luis y Fernando; el 1.0 que
    # pone Odoo por omision parece un precio de un peso.
    # El nombre NO necesita entrada aparte en es_MX: es el mismo texto en los
    # dos idiomas y Odoo sirve el base cuando no hay traduccion distinta.
    # Comprobado leyendolo con usuarios reales en es_MX.
    if gog.list_price:
        gog.write({'list_price': 0.0})
        print('[ok] precio de venta a 0 (lo definen Luis y Fernando)')

    print('    categoria=%s destino=%s trazabilidad=%s vender=%s comprar=%s unidad=%s' % (
        gog.categ_id.complete_name, gog.amunet_destino_almacen, gog.tracking,
        gog.sale_ok, gog.purchase_ok, gog.uom_id.name))
    print('    va a distribucion (calculado): %s' % gog.amunet_va_a_distribucion)
    print('    nombre en espanol: %s | precio de venta: %s' % (
        gog.with_context(lang='es_MX').name, gog.list_price))
    print('    existencia: %s (debe ser 0)' % gog.qty_available)

env.cr.commit()
