# -*- coding: utf-8 -*-
"""Alta de los 13 BoM de almohadillas SPALMA, con sus actividades y su etapa.

Idempotente: se puede correr las veces que haga falta. Sirve para dos cosas --
recrear esto en staging despues de un clon de produccion (los datos de staging
se reemplazan y estos BoM se perderian) y promoverlo a produccion.

  docker cp alta_boms_almohadillas.py odoo-staging:/tmp/x.py
  docker exec odoo-staging bash -c 'odoo shell -c /etc/odoo/odoo.conf \
    -d Amunet_testing --no-http --db_host $HOST --db_port $PORT \
    --db_user $USER --db_password $PASSWORD < /tmp/x.py'

DATOS VALIDADOS POR MERY EL 22-SEP-2026
---------------------------------------
El BoM es POR LAMINA: produce las tiras que salen de una lamina y consume la
lamina entera. La lamina se sumerge, se seca y se corta completa; no se trabaja
"una tira".

Rendimiento: NO es el maximo teorico en las de conjugado. La cortadora no
alcanza las ultimas tiras de la lamina, asi que de 20 cm a 0.7 salen 26 y no 28.
Esa merma va DENTRO del BoM a proposito.

Secado: 4 horas a 37 C en todas. El tiempo de ciclo se reparte entre las tiras
de la lamina para que el total por lamina de 4 h.

Solucion: 50 ml por lamina (60 en las Biotech), que es lo que cuesta cada lamina
ADICIONAL. La carga inicial de la charola -- 150 ml mas, para completar los 200
de la primera -- no cabe en un BoM porque este solo multiplica, asi que va
escrita en la actividad de pretratado, donde el operador la lee. La solucion se
desecha al terminar: no regresa a almacen.

Desecante: 2 por lamina, SOLO en las pretratadas.

Actividades: la revision del corte y el empaque los hace el mismo operador, ahi
mismo en Laminado, Secado y Corte -- el material no se mueve. La conciliacion NO
va aqui: ya es un paso del flujo de la orden.

PENDIENTE: A8 (orina) y A9 (PVP + NaOH) se crean SIN linea de solucion porque
esas dos soluciones aun no estan dadas de alta. No se pueden fabricar hasta que
existan.
"""
P = env['product.product'].sudo()
T = env['product.template'].sudo()
B = env['mrp.bom'].sudo()
WC = env['mrp.workcenter'].sudo()

UOM_ML = env.ref('uom.product_uom_milliliter', raise_if_not_found=False) \
    or env['uom.uom'].sudo().search([('name', '=', 'ml')], limit=1)
c_mp = WC.search([('name', '=', 'Almacén Materia Prima')], limit=1)
c_lsc = WC.search([('name', '=', 'Laminado, Secado y Corte')], limit=1)
assert c_mp and c_lsc, 'faltan los centros base (Almacen MP / Laminado, Secado y Corte)'

# Lectura y Pretratamiento se creo en staging el 21-sep-2026 y NO existe en
# produccion. Se crea aqui si falta, para que el script sirva en los dos lados
# sin depender del orden en que se corran las cosas.
c_lyp = WC.search(['|', ('name', '=', 'Lectura y Pretratamiento'),
                   ('code', '=', 'LYP')], limit=1)
if not c_lyp:
    c_lyp = WC.create({
        'name': 'Lectura y Pretratamiento', 'code': 'LYP', 'active': True,
        'time_efficiency': 100.0, 'costs_hour': 0.0,
        'note': 'Lectura de D.O. de conjugado, pretratado y secado de '
                'almohadillas. Mismo espacio fisico que Soluciones, sin '
                'separacion. Equipos: Agitador orbital (88) y Horno SLW-53 (90). '
                'Datos de Jorge (Ensayo), 18-sep-2026.',
    })
    print('   CREADO el centro de trabajo Lectura y Pretratamiento')
assert UOM_ML, 'falta la unidad ml'

ML_CARGA = 150.0          # lo que se queda en la charola y se desecha
SECADO_MIN = 240.0        # 4 h por lamina

# clave, alias, tiras/lamina, lamina, ancho cm, solucion (None = falta de alta), ml por lamina
ALMOHADILLAS = [
    ('SPALMA01', 'A1',  26, 'MPAFV01', 0.7, 'SPSPA01', 50),
    ('SPALMA02', 'A2',  26, 'MPAFV01', 0.7, False,     0),
    ('SPALMA03', 'A3',  37, 'MPAFV01', 0.5, 'SPSPA01', 50),
    ('SPALMA04', 'A4',  14, 'MPAFV01', 1.4, 'SPSPA03', 50),
    ('SPALMA05', 'A5',  14, 'MPAFV01', 1.4, False,     0),
    ('SPALMA06', 'A6',  19, 'MPAFV02', 1.1, 'SPSPA02', 60),
    ('SPALMA07', 'A7',  19, 'MPAFV02', 1.1, False,     0),
    ('SPALMA08', 'A8',   4, 'MPAFV02', 5.0, None,      60),
    ('SPALMA09', 'A9',  66, 'MPAFV01', 0.3, None,      50),
    ('SPALMA10', 'A10', 66, 'MPAFV01', 0.3, False,     0),
    ('SPALMA11', 'A11', 11, 'MPAAB01', 1.7, False,     0),
    ('SPALMA12', 'A12',  6, 'MPAAB01', 3.0, False,     0),
    ('SPALMA13', 'A13', 35, 'MPAGR01', 0.7, False,     0),
]


def buscar(cod):
    return P.search([('default_code', '=', cod)], limit=1)


creados = omitidos = 0
for cod, alias, tiras, mp, ancho, sol, ml in ALMOHADILLAS:
    prod = buscar(cod)
    if not prod:
        print('   %-9s NO EXISTE el producto, se omite' % cod)
        continue

    # la etapa: sin ella el producto no aparece al crear la orden
    if 'amunet_etapa_ll' in T._fields and prod.product_tmpl_id.amunet_etapa_ll != 'pretratado':
        prod.product_tmpl_id.write({'amunet_etapa_ll': 'pretratado'})

    if B.search([('product_tmpl_id', '=', prod.product_tmpl_id.id)], limit=1):
        print('   %-9s ya tiene BoM, se omite' % cod)
        omitidos += 1
        continue

    lam = buscar(mp)
    assert lam, 'falta la lamina %s' % mp
    pretrata = sol is not False           # False = solo corta; None = pretrata sin solucion de alta

    lineas = [(0, 0, {'product_id': lam.id, 'product_qty': 1.0,
                      'product_uom_id': lam.uom_id.id})]
    ops = [(0, 0, {'name': 'Surtido de materiales - Almohadilla %s' % alias,
                   'workcenter_id': c_mp.id, 'sequence': 5, 'time_cycle_manual': 0.01})]

    if pretrata:
        des = buscar('STDSC01')
        assert des, 'falta el desecante STDSC01'
        lineas.append((0, 0, {'product_id': des.id, 'product_qty': 2.0,
                              'product_uom_id': des.uom_id.id}))
        if sol:
            s = buscar(sol)
            assert s, 'falta la solucion %s' % sol
            lineas.append((0, 0, {'product_id': s.id, 'product_qty': float(ml),
                                  'product_uom_id': UOM_ML.id}))
            nota = '%s: %g ml la 1a lamina, +%d ml por lamina extra' % (sol, ML_CARGA + ml, ml)
        else:
            nota = 'SOLUCION PENDIENTE DE ALTA'
        ops += [
            (0, 0, {'name': 'Pretratado: sumergir en %s - Almohadilla %s' % (nota, alias),
                    'workcenter_id': c_lyp.id, 'sequence': 10,
                    'time_cycle_manual': 30.0 / tiras}),
            (0, 0, {'name': 'Secado 4 h a 37 C - Almohadilla %s' % alias,
                    'workcenter_id': c_lsc.id, 'sequence': 20,
                    'time_cycle_manual': SECADO_MIN / tiras}),
        ]

    ops += [
        (0, 0, {'name': 'Corte a %g cm - Almohadilla %s' % (ancho, alias),
                'workcenter_id': c_lsc.id, 'sequence': 30, 'time_cycle_manual': 0.16}),
        (0, 0, {'name': 'Revision del corte - Almohadilla %s' % alias,
                'workcenter_id': c_lsc.id, 'sequence': 40, 'time_cycle_manual': 0.05}),
        (0, 0, {'name': 'Empaque%s - Almohadilla %s' % (
                    ' con desecante (2 por lamina)' if pretrata else '', alias),
                'workcenter_id': c_lsc.id, 'sequence': 50, 'time_cycle_manual': 0.05}),
        (0, 0, {'name': 'Entrega a almacen - Almohadilla %s' % alias,
                'workcenter_id': c_mp.id, 'sequence': 60, 'time_cycle_manual': 0.005}),
    ]

    bom = B.create({
        'product_tmpl_id': prod.product_tmpl_id.id,
        'product_qty': float(tiras),
        'product_uom_id': prod.uom_id.id,
        'type': 'normal',
        'code': '%s-%s' % ('PRETRATA' if pretrata else 'CORTE', cod),
        'bom_line_ids': lineas,
        'operation_ids': ops,
    })
    creados += 1
    print('   %-9s %-18s produce %2d <- 1 %s%s' % (
        cod, bom.code, tiras, mp,
        (' + 2 desecantes' + (' + %d ml %s' % (ml, sol) if sol else ' [SIN SOLUCION]')) if pretrata else ''))

env.flush_all()
env.cr.commit()
print('CREADOS: %d   YA EXISTIAN: %d' % (creados, omitidos))
