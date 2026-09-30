# -*- coding: utf-8 -*-
"""Los 5 pasos de la linea Llenado de Viales en las 12 recetas.

DE DONDE SALEN. Diseno cerrado con Mery el 24-sep-2026:

     5  Surtido de materiales   Almacen Materia Prima
    10  Lavado y secado         Soluciones
    20  Llenado                 Soluciones
    30  Cierre                  Soluciones
    40  Producir                Soluciones   <- captura cuanto entrega

Sin etiquetado: eso pasa hasta Acondicionado, no en esta linea.

POR QUE HACEN FALTA. Hasta hoy las 12 recetas tenian componentes y CERO
operaciones, asi que la orden no generaba ordenes de trabajo: el operador
llegaba a una pantalla sin pasos y no tenia donde asentar que ya lavo, que ya
lleno y que ya cerro. Para Cofepris el registro de lo hecho no es opcional.

LOS TIEMPOS van en fraccion de minuto POR PIEZA, que es la escala que ya usan
las rutas de linea corta (DMCRD01: surtido 0.01, operacion 0.08-0.16, resguardo
0.005). La receta produce 1 pieza, asi que un 1.0 aqui se multiplicaria por las
20,000 piezas de una orden y la planeacion de centros quedaria inservible.

Idempotente: si el paso ya existe con el mismo centro y tiempo, no lo toca.
"""
PASOS = [
    (5,  'Surtido de materiales',                     'AMP', 0.01),
    (10, 'Lavado y secado del vial',                  'SOL', 0.08),
    (20, 'Llenado',                                   'SOL', 0.08),
    (30, 'Cierre',                                    'SOL', 0.08),
    (40, 'Entrega a almacen (queda en espera de analisis)', 'SOL', 0.005),
]

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

centros = {}
for code in ('AMP', 'SOL'):
    w = env['mrp.workcenter'].search([('code', '=', code)], limit=1)
    assert w, 'No existe el centro de trabajo %s' % code
    centros[code] = w

viales = env['product.template'].search([('amunet_etapa_ll', '=', 'llenado')])
print('viales de la etapa llenado: %d' % len(viales))

creados, ajustados, saltados = [], [], []
for tmpl in viales.sorted(lambda t: t.default_code or ''):
    clave = tmpl.default_code or tmpl.name
    boms = env['mrp.bom'].search([('product_tmpl_id', '=', tmpl.id)])
    if len(boms) != 1:
        saltados.append((clave, '%d recetas' % len(boms)))
        continue
    b = boms
    for seq, texto, code, minutos in PASOS:
        nombre = '%s - %s' % (texto, clave)
        ya = b.operation_ids.filtered(lambda o: o.sequence == seq)
        if ya:
            op = ya[0]
            cambios = {}
            if op.name != nombre:
                cambios['name'] = nombre
            if op.workcenter_id != centros[code]:
                cambios['workcenter_id'] = centros[code].id
            if abs((op.time_cycle_manual or 0) - minutos) > 1e-6:
                cambios['time_cycle_manual'] = minutos
            if cambios:
                op.write(cambios)
                ajustados.append((clave, seq, ', '.join(cambios)))
            continue
        env['mrp.routing.workcenter'].create({
            'bom_id': b.id,
            'sequence': seq,
            'name': nombre,
            'workcenter_id': centros[code].id,
            'time_cycle_manual': minutos,
        })
        creados.append((clave, seq, texto))

env.cr.commit()

print('=' * 84)
print('PASOS CREADOS: %d' % len(creados))
for clave, seq, texto in creados:
    print('   %-9s %3s  %s' % (clave, seq, texto))
print('-' * 84)
print('AJUSTADOS: %d' % len(ajustados))
for clave, seq, que in ajustados:
    print('   %-9s %3s  %s' % (clave, seq, que))
print('-' * 84)
print('SALTADOS: %d' % len(saltados))
for clave, motivo in saltados:
    print('   %-9s %s' % (clave, motivo))
print('=' * 84)
