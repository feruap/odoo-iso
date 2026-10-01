# -*- coding: utf-8 -*-
"""PTBWP01 y PTESP01: darles ruta, y replanificar la orden 180 que estaba trabada.

EL SINTOMA. En la orden 0926/01/BWE (id 180) no aparecia el boton "Iniciar Surtido".
No era permisos ni cache del navegador.

LA CAUSA. El boton exige cuatro cosas y tres fallaban por la misma raiz:

    state in (confirmed, progress, to_close)    OK
    amunet_supply_workorder_id                  FALLA: no habia ninguna
    amunet_supply_state == 'pending'            FALLA: sin valor
    is_planned, o ser una solucion              FALLA: no planificada

La receta ACOND-PTBWP01 se creo el 22-sep SIN RUTA. Sin operaciones, Odoo no genera
ordenes de trabajo; sin ordenes de trabajo no hay surtido que iniciar y la orden
tampoco se puede planificar. PTESP01 estaba igual y le habria pasado lo mismo en su
primera orden.

Hay 155 recetas activas sin ruta, pero solo esta orden estaba trabada: las demas son
casi todas soluciones, y las soluciones estan exentas a proposito -- tienen su propio
flujo de boton unico, y por eso la condicion del boton incluye
amunet_is_solution_product-.

LA RUTA: SEIS PASOS, NO SIETE. Se copia el patron de los reenvasados (PTREC04-13,
medios de cultivo) quitando dos pasos que aqui no existen:

    - "Pesado" en Soluciones: las bolsas y las esponjas se cuentan, no se pesan.
    - "Ingreso de REACTIVO en empaque primario": no hay reactivo. Se renombra a
      "Ingreso de producto en empaque primario".

No falta un paso de esterilizacion: el componente de las dos recetas es COBPE01
"Bolsa Whirl-Pak esterilizada", o sea que llega esteril de compra. En todo el sistema
no existe ninguna operacion de esterilizacion.

La secuencia 20 se deja VACIA a proposito: asi se ve de un golpe, comparando con sus
hermanas de familia, que el pesado falta porque no aplica y no porque se olvido.

EL PASO DE SURTIDO SE RECONOCE POR EL CODIGO DEL CENTRO, no por su nombre: el compute
busca la operacion cuyo workcenter tiene code = 'AMP'. Un paso llamado "Surtido de
materiales" en otro centro NO activaria el boton.

Los tiempos son los de su familia (reenvasados), no 1 minuto: estos productos se
acondicionan igual que un reenvase, y asi la planeacion de centros queda coherente.

Idempotente: no duplica operaciones si ya estan.
"""

# (secuencia, nombre del paso, codigo del centro, horas)
PASOS = [
    (5,  'Surtido de materiales',                          'AMP', 0.01),
    (10, 'Impresion/etiquetado de empaque primario',       'AC2', 0.08),
    # la 20 (Pesado, en Soluciones) no aplica: aqui se cuenta, no se pesa
    (30, 'Ingreso de producto en empaque primario',        'AC1', 0.08),
    (40, 'Sellado/cerrado de empaque',                     'AC1', 0.08),
    (50, 'Colocacion de empaque primario en secundario',   'AC2', 0.08),
    (60, 'Resguardo de producto terminado',                'PTT', 0.005),
]
RECETAS = ['ACOND-PTBWP01', 'ACOND-PTESP01']

centros = {}
for code in ('AMP', 'AC1', 'AC2', 'PTT'):
    wc = env['mrp.workcenter'].search([('code', '=', code)], limit=1)
    assert wc, 'no existe el centro de trabajo con codigo %s' % code
    centros[code] = wc
print('centros: %s' % ', '.join('%s=%s' % (c, w.name) for c, w in centros.items()))

for codigo in RECETAS:
    bom = env['mrp.bom'].search([('code', '=', codigo)], limit=1)
    if not bom:
        print('\n[!] no existe la receta %s' % codigo)
        continue
    prod = bom.product_tmpl_id
    corto = prod.nombre_etiqueta or prod.name
    print('\n%s  (%s)' % (codigo, prod.default_code))
    for seq, nombre, code, horas in PASOS:
        titulo = '%s - %s' % (nombre, corto)
        ya = bom.operation_ids.filtered(lambda o: o.workcenter_id == centros[code]
                                        and (o.name or '').startswith(nombre))
        if ya:
            print('   [=] %2d  %s' % (seq, titulo[:66]))
            continue
        env['mrp.routing.workcenter'].create({
            'bom_id': bom.id,
            'name': titulo,
            'workcenter_id': centros[code].id,
            'sequence': seq,
            'time_mode': 'manual',
            'time_cycle_manual': horas,
        })
        print('   [+] %2d  %-62s %s' % (seq, titulo[:62], code))

env.cr.commit()

# --- la orden 180: generar sus ordenes de trabajo y planificar ---
#
# POR QUE NO SE REGRESA A BORRADOR, que seria la via nativa: el compute del core
# (_compute_workorder_ids) solo actua en estado draft -- "if production.state != 'draft':
# continue"- y Odoo 19 ya no tiene action_back_to_draft. Pero sobre todo, reconfirmar
# vuelve a explotar la receta, y el empaque secundario COBME02 de esta orden NO viene de
# la receta: viene de la PRESENTACION, y se agrega al aprobar el plan de empaque.
# Regresar a borrador lo perderia y la orden se quedaria sin su caja.
#
# Tampoco existe _create_workorder() en Odoo 19 (se probo y truena). Asi que se crean con
# los mismos valores que pone el core y despues se ligan a los movimientos, que es lo que
# permite al surtido saber que material corresponde a cada paso.

mo = env['mrp.production'].browse(180)
print('\n=== ORDEN %s ===' % mo.name)
print('  antes: state=%s  ordenes de trabajo=%s  planificada=%s' % (
    mo.state, len(mo.workorder_ids), mo.is_planned))

creadas = 0
for op in mo.bom_id.operation_ids.sorted('sequence'):
    if mo.workorder_ids.filtered(lambda w: w.operation_id == op):
        continue
    env['mrp.workorder'].create({
        'name': op.name,
        'production_id': mo.id,
        'workcenter_id': op.workcenter_id.id,
        'product_uom_id': mo.product_uom_id.id,
        'operation_id': op.id,
        'state': 'ready',
    })
    creadas += 1
    print('   [+] %-64s [%s]' % ((op.name or '')[:64], op.workcenter_id.code or '?'))

if creadas:
    mo._link_workorders_and_moves()
env.cr.commit()
mo.invalidate_recordset()

if not mo.is_planned:
    mo.button_plan()
    env.cr.commit()
    print('   planificada')
mo.invalidate_recordset()

print('\n=== COMO QUEDO LA 180 ===')
print('  state                      = %r' % mo.state)
print('  ordenes de trabajo         = %s' % len(mo.workorder_ids))
for w in mo.workorder_ids.sorted('id'):
    print('      [%s] %-56s %-4s %s' % (w.id, (w.name or '')[:56], w.workcenter_id.code or '?', w.state))
print('  is_planned                 = %r' % mo.is_planned)
print('  amunet_supply_workorder_id = %r' % (mo.amunet_supply_workorder_id.id or False))
print('  amunet_supply_state        = %r' % mo.amunet_supply_state)
print('  material de la orden (no se toco):')
for m in mo.move_raw_ids.sorted('id'):
    print('      %-9s pedido=%-7s surtido=%-5s state=%s' % (
        m.product_id.default_code, m.product_uom_qty, m.amunet_qty_supplied, m.state))

visible = (mo.state in ('confirmed', 'progress', 'to_close')
           and mo.amunet_supply_workorder_id
           and mo.amunet_supply_state == 'pending'
           and (mo.is_planned or mo.amunet_is_solution_product))
print('\n  BOTON "Iniciar Surtido": %s' % ('YA APARECE' if visible else 'SIGUE SIN APARECER -- revisar'))
