# -*- coding: utf-8 -*-
"""PTBWP01 deja de requerir analisis de Calidad, por ahora.

POR QUE. La orden 0926/01/BWE (10 paquetes de bolsas Whirl-Pak) no puede cerrarse: su
"Integracion de Calidad" dice "Pendiente de Solicitar" y el cierre exige que el analisis
este aprobado. Pero PTBWP01 NO TIENE UN SOLO PARAMETRO DE CALIDAD CONFIGURADO: si alguien
solicitara el analisis, nacería vacio, sin un renglon que capturar. El letrero pide algo
que no se puede hacer.

Decision de Mery, 02-oct-2026: liberar este producto sin analisis mientras Calidad no
defina su especificacion.

ALCANCE REAL, y no es por orden: el campo de la orden (amunet_sys_req_qc) es un related
SIN almacenar sobre product.amunet_req_quality_control. Se comprobo en staging: apagarlo
en una orden apaga EL PRODUCTO y con el todas sus ordenes, presentes y futuras. No existe
forma de apagarlo solo para esta orden.

LO QUE ESTO DESACTIVA, para que quede claro en el expediente:
  - el bloqueo para CERRAR la orden sin analisis aprobado
  - el candado de SALIDA A CLIENTE de los lotes de este producto: ese candado se salta
    los productos que no requieren analisis, asi que las 10 piezas podran venderse sin
    pasar por Calidad

PENDIENTE QUE QUEDA ABIERTO: cuando Calidad defina los parametros de PTBWP01, hay que
volver a encender esta bandera. No se enciende sola. PTESP01 esta en el mismo caso (sin
parametros) y NO se toca aqui: no se pidio.
"""

CLAVE = 'PTBWP01'
ORDEN = '0926/01/BWE'

tmpl = env['product.template'].search([('default_code', '=', CLAVE)], limit=1)
assert tmpl, 'no existe %s' % CLAVE
mo = env['mrp.production'].search([('name', '=', ORDEN)], limit=1)
assert mo, 'no existe la orden %s' % ORDEN

params = env['amunet.quality.parameter.product.rel'].search([
    ('product_tmpl_id', '=', tmpl.id), ('active', '=', True)])
print('%s   requiere analisis: %s   parametros de calidad configurados: %s' % (
    CLAVE, tmpl.amunet_req_quality_control, len(params)))
print('%s   state=%s   integracion de calidad=%s' % (
    mo.name, mo.state, mo.quality_analysis_status))

if not tmpl.amunet_req_quality_control:
    print('\nya estaba apagado')
else:
    assert not params, (
        'OJO: el producto SI tiene %s parametro(s) de calidad configurados. '
        'Entonces el analisis si se puede hacer y no procede apagar la bandera.' % len(params))
    tmpl.amunet_req_quality_control = False
    print('\n  apagado: %s ya no requiere analisis de Calidad' % CLAVE)

    tmpl.message_post(body=(
        '<p><b>Deja de requerir analisis de Calidad</b> (decision de Mery, 02-oct-2026).</p>'
        '<p>Motivo: el producto no tiene ningun parametro de calidad configurado, asi que '
        'un analisis solicitado nacería vacio. La orden 0926/01/BWE no podia cerrarse por '
        'un requisito que no se podia cumplir.</p>'
        '<p><b>Esto tambien desactiva el candado de salida a cliente</b> para los lotes de '
        'este producto: podran venderse sin pasar por Calidad.</p>'
        '<p><b>Pendiente:</b> cuando Calidad defina la especificacion de este producto, hay '
        'que volver a encender esta bandera. No se enciende sola.</p>'))

env.cr.commit()

mo.invalidate_recordset(); tmpl.invalidate_recordset()
print('\n=== COMO QUEDO ===')
print('  %s requiere analisis: %s' % (CLAVE, tmpl.amunet_req_quality_control))
print('  %s integracion de calidad: %s' % (mo.name, mo.quality_analysis_status))
print('  state de la orden: %s' % mo.state)

if mo.quality_analysis_status == 'none':
    mo.message_post(body=(
        '<p>La <b>Integracion de Calidad</b> de esta orden paso a <b>No requerido</b>.</p>'
        '<p>PTBWP01 no tiene parametros de calidad configurados, asi que el analisis que '
        'pedia este letrero no se podia hacer: nacería vacio. Mery autorizo liberar el '
        'producto sin analisis el 02-oct-2026, mientras Calidad define su especificacion.</p>'
        '<p>Ojo: con esto el lote de esta orden puede salir a cliente sin pasar por '
        'Calidad. Si estas 10 piezas no deben venderse todavia, hay que detenerlas por '
        'otra via.</p>'))
    env.cr.commit()
    print('  nota puesta en la orden')

otras = env['mrp.production'].search([('product_id.product_tmpl_id', '=', tmpl.id)])
print('\n  ordenes de este producto afectadas por el cambio: %s' % len(otras))
for o in otras:
    print('     %-14s %-10s integracion de calidad=%s' % (o.name, o.state, o.quality_analysis_status))
