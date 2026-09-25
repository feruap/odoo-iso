# MO 151 (0926/01/HCG) seguia ofreciendo "Solicitar analisis" aunque el lote ya
# estaba APROBADO. No era un error de la pantalla: el sistema veia 15 piezas sin
# cubrir por ningun analisis.
#
# ORIGEN. Secuencia del lote:
#   21-sep  se produjeron 1,100 pz
#   21-sep  analisis PARCIAL de 260 pz (QC/2026/00480)
#   23-sep  ese analisis se ARCHIVA: se habia pedido con la cantidad equivocada
#   23-sep  analisis COMPLETO declarando 1,045 pz (QC/2026/00482)
#   23-sep  correccion: "la cantidad real son 1,060, no 1,045"
#   24-sep  QC/2026/00482 finalizado, lote APROBADO
#
# La correccion del 23-sep arreglo la ORDEN (qty_producing y
# amunet_pt_qty_solicitada quedaron en 1,060) pero NO el analisis, que se quedo
# amparando 1,045. De ahi los 15 de diferencia.
#
# El boton se oculta solo cuando el analisis esta aprobado Y no quedan piezas sin
# cubrir; con 15 pendientes seguia apareciendo, y hacia bien.
#
# QC/2026/00482 SI cubrio el lote completo: se pidio como "completo" y se aprobo.
# Se corrige lo que ampara para que coincida con lo fabricado.
#
# No se toca estado, lote, producto ni archivado, que son los campos que exigen
# 'Razon de cambio'. Se deja constancia en el chatter del analisis y de la orden.

CHECK, MO, NUEVO = 'QC/2026/00482', 151, 1060.0

qc = env['amunet.quality.check'].sudo().search([('name', '=', CHECK)], limit=1)
assert qc, 'no existe %s' % CHECK
mo = env['mrp.production'].browse(MO)
assert qc.amunet_production_id == mo, 'el analisis no es de la orden %s' % MO

antes = qc.amunet_qty_analizada
print('orden            : %s' % mo.name)
print('fabricadas       : %s' % mo.amunet_pt_qty_solicitada)
print('ampara ANTES     : %s' % antes)
print('sin analizar     : %s' % mo.amunet_pt_qty_sin_analizar)

if antes == NUEVO:
    print('\nya estaba en %s, no hay nada que hacer' % NUEVO)
else:
    qc.write({'amunet_qty_analizada': NUEVO})
    texto = (
        'Correccion 25-sep-2026: este analisis amparaba <b>%s</b> pieza(s) y el '
        'lote fabrico <b>%s</b>. La diferencia viene de la correccion del '
        '23-sep, que ajusto la cantidad en la orden pero no aqui. Se corrige a '
        '<b>%s</b>: este analisis se pidio como COMPLETO y se aprobo, asi que '
        'cubre el lote entero. Sin esto la orden seguia ofreciendo "Solicitar '
        'analisis" por 15 piezas que ningun analisis cubria.'
    ) % (antes, NUEVO, NUEVO)
    qc.message_post(body=texto)
    mo.message_post(body=texto)
    env.cr.commit()
    print('\nampara AHORA     : %s' % qc.amunet_qty_analizada)

mo.invalidate_recordset()
print('sin analizar     : %s' % mo.amunet_pt_qty_sin_analizar)
cond = (mo.state not in ('to_close', 'done') or not mo.amunet_sys_req_qc
        or mo.amunet_es_desarrollo or not mo.amunet_puede_pedir_analisis
        or (mo.quality_analysis_status in ('requested', 'approved')
            and mo.amunet_pt_qty_sin_analizar <= 0))
print('el boton queda   : %s' % ('OCULTO' if cond else '*** TODAVIA VISIBLE ***'))
