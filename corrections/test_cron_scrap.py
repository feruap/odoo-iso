import traceback
try:
    scrap_ant = env['stock.scrap'].search([('lot_id.name','=','HMC02-TEST-VENCE-PRONTO')], limit=1)
    if scrap_ant:
        scrap_ant.sudo().write({'state': 'cancel'})
        print("Descarte anterior cancelado")

    env['stock.lot']._amunet_scrap_hojas_por_vencer()
    env.cr.commit()
    print("Cron ejecutado OK")

    scrap = env['stock.scrap'].search([
        ('lot_id.name','=','HMC02-TEST-VENCE-PRONTO'),
        ('state','=','draft')
    ], limit=1)
    print(f"Descarte: {'CREADO — ' + scrap.name if scrap else 'NO CREADO'}")
    if scrap:
        acts = env['mail.activity'].search([('res_id','=',scrap.id),('res_model','=','stock.scrap')])
        print(f"Actividades: {len(acts)}")
        for a in acts:
            print(f"  Resumen: {a.summary}")
            print(f"  Para: {a.user_id.name}")
except Exception as e:
    traceback.print_exc()
