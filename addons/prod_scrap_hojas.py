import os, traceback
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

if os.environ.get('RUN_CORRECTION_FORCE_PROD') != 'yes-i-know-what-i-do':
    print("PROTECCION activa"); import sys; sys.exit(0)

MESES = 6
hoy = date.today()
limite = hoy + relativedelta(months=MESES)
limite_dt = datetime(limite.year, limite.month, limite.day, 23, 59, 59)
print("Hoy: " + str(hoy) + " | Limite 6 meses: " + str(limite))

try:
    cat = env['product.category'].search([('name','=','Hoja maestra')], limit=1)
    cat_ids = env['product.category'].search([('id','child_of',cat.id)]).ids

    lotes = env['stock.lot'].search([
        ('product_id.categ_id','in',cat_ids),
        ('expiration_date','!=',False),
        ('expiration_date','<=',str(limite_dt)),
    ])
    print("Lotes dentro del rango: " + str(len(lotes)))

    usuario = env['res.users'].browse(78)
    tipo_act = env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
    creados = []

    for lote in lotes:
        ya_existe = env['stock.scrap'].search([
            ('lot_id','=',lote.id),
            ('state','not in',('done','cancel')),
        ], limit=1)
        if ya_existe:
            print("Ya existe descarte para " + lote.name)
            continue

        quants = env['stock.quant'].search([
            ('lot_id','=',lote.id),
            ('quantity','>',0),
            ('location_id.usage','=','internal'),
        ])
        if not quants:
            continue

        for quant in quants:
            scrap = env['stock.scrap'].sudo().create({
                'product_id': lote.product_id.id,
                'product_uom_id': lote.product_id.uom_id.id,
                'lot_id': lote.id,
                'scrap_qty': quant.quantity,
                'location_id': quant.location_id.id,
            })
            exp_str = lote.expiration_date.strftime('%d/%m/%Y')
            creados.append(lote.product_id.default_code + " | " + lote.name + " | " + str(round(quant.quantity,1)) + " " + lote.product_id.uom_id.name + " | vence " + exp_str)
            print("  Descarte: " + (scrap.name or 'borrador') + " — " + creados[-1])

            if tipo_act:
                lote.sudo().activity_schedule(
                    activity_type_id=tipo_act.id,
                    summary='Confirmar descarte — ' + lote.product_id.display_name + ' vence ' + exp_str,
                    note=(
                        'Hoja Maestra por vencer (menos de ' + str(MESES) + ' meses).<br/>'
                        'Lote: <b>' + lote.name + '</b> | Cantidad: ' + str(round(quant.quantity,1)) + ' ' + lote.product_id.uom_id.name + '<br/>'
                        'Ubicacion: ' + quant.location_id.complete_name + '<br/>'
                        'Caducidad: <b>' + exp_str + '</b><br/><br/>'
                        'Revisa y valida el descarte en Inventario -> Operaciones -> Descartes.'
                    ),
                    user_id=usuario.id,
                )

    env.cr.commit()
    print("")
    print("Total descartes creados: " + str(len(creados)))

except Exception:
    traceback.print_exc()
