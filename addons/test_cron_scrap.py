import traceback
try:
    scrap_ant = env['stock.scrap'].search([('lot_id.name','=','HMC02-TEST-VENCE-PRONTO')], limit=1)
    if scrap_ant and scrap_ant.state == 'draft':
        scrap_ant.sudo().unlink()
        print("Descarte anterior eliminado")

    env['stock.lot']._amunet_scrap_hojas_por_vencer()
    env.cr.commit()
    print("Cron ejecutado OK")

    scrap = env['stock.scrap'].search([('lot_id.name','=','HMC02-TEST-VENCE-PRONTO'),('state','=','draft')], limit=1)
    if scrap:
        print("Descarte CREADO: " + (scrap.name or 'borrador'))
        print("  Producto: " + scrap.product_id.display_name)
        print("  Cantidad: " + str(scrap.scrap_qty) + " " + scrap.product_uom_id.name)

    lote = env['stock.lot'].search([('name','=','HMC02-TEST-VENCE-PRONTO')], limit=1)
    acts = env['mail.activity'].search([('res_id','=',lote.id),('res_model','=','stock.lot')])
    print("Actividades en el lote: " + str(len(acts)))
    for a in acts:
        print("  Resumen: " + (a.summary or ''))
        print("  Para: " + a.user_id.name)
        print("  Nota: " + (a.note or ''))
except Exception:
    traceback.print_exc()
