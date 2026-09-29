"""Cuantas tiras aparta para Calidad cada hoja maestra que laminamos aqui.

Dato de Diana (29-sep-2026, msg 18:19 + correccion 18:22), autorizado por Mery.

    Base: siempre negativo + positivo             = 2 tiras
    Sangre / suero / plasma:      +1 extra        = 3 tiras
    Flu / Covid / RSV (reactividad): +1 extra     = 3 tiras
    Sin replica en ningun caso

POR QUE VA EN CENTIMETROS Y NO EN TIRAS: el sistema mide las hojas maestras en cm -- la
hoja son 30 cm y el corte es a 0.3 cm. No existe una unidad "tira", y si la hubiera el
sistema no podria reservar ni descontar el material. Asi que la cantidad se guarda en cm
y el numero de tiras va escrito en el nombre del plan y en la nota, que es lo que lee
quien muestrea:

    3 tiras  =  0.9 cm
    2 tiras  =  0.6 cm

DONDE VIVE: en los planes de muestreo, familia 'Hoja impregnada / hoja maestra', etapa
PROCESO. La etapa importa: cuando el analisis nace de una orden de fabricacion el
picking es interno y la etapa sale 'proceso'; cuando la hoja se COMPRA el picking es de
entrada y la etapa sale 'recepcion'. Los dos planes nuevos son de proceso, asi que las
hojas compradas siguen con su muestreo AQL de recepcion y no se tocan.

El analisis toma la cantidad solo, sin que nadie la escriba: al crearse busca el plan
aplicable, calcula la muestra sugerida, la copia a 'Cantidad de muestreo' y avisa si
alguien la cambia.

Idempotente.
"""
Plan = env['amunet.quality.sampling.plan'].sudo()
Prod = env['product.product'].sudo()

TRES = ['SPHMC01', 'SPHMC15', 'SPHMC20', 'SPHMC18', 'SPHMC19', 'SPHMC22', 'SPHMC23',
        'SPHMC07', 'SPHMC24', 'SPHMC38', 'SPHMC37', 'SPHMC52']
DOS = ['SPHMC09', 'SPHMT01', 'SPHMC45']

RAZON_3 = (
    'Diana, 29-sep-2026. Dos tiras de base (una negativa y una positiva) mas una tercera '
    'por ser muestra de sangre, suero o plasma, o por la lectura de reactividad en '
    'Influenza, Covid y RSV. Sin replica.\n\n'
    '3 tiras x 0.3 cm de corte = 0.9 cm de hoja.')
RAZON_2 = (
    'Diana, 29-sep-2026. Las dos tiras de base: una negativa y una positiva. Sin extra y '
    'sin replica.\n\n'
    '2 tiras x 0.3 cm de corte = 0.6 cm de hoja.\n\n'
    'Vitamina D (SPHMC09) entra aqui por correccion expresa de Diana del mismo dia: '
    'aunque es muestra de suero, lleva 2 tiras y no 3.')
NOTA = ('Se cortan %d tiras de 0.3 cm de la misma hoja laminada y se entregan a Calidad. '
        'El sistema lo pide en centimetros porque la hoja se mide en cm: %s cm en total.')

PLANES = (
    ('SMP-HM-PRO-3T', 'Hoja maestra laminada - muestreo para Calidad (3 tiras)', 0.9, TRES, RAZON_3),
    ('SMP-HM-PRO-2T', 'Hoja maestra laminada - muestreo para Calidad (2 tiras)', 0.6, DOS, RAZON_2),
)

for code, nombre, cm, claves, razon in PLANES:
    tiras = int(round(cm / 0.3))
    faltan = [c for c in claves if not Prod.search([('default_code', '=', c)], limit=1)]
    prods = Prod.search([('default_code', 'in', claves)])
    vals = {
        'name': nombre,
        'code': code,
        'family': 'uncut_sheet',
        'stage': 'in_process',
        'method': 'fixed',
        'fixed_qty': cm,
        'min_qty': 0.0,
        'max_qty': 0.0,
        'lot_min': 0.0,
        'lot_max': 0.0,
        'sequence': 5,
        'active': True,
        'product_ids': [(6, 0, prods.ids)],
        'functional_sample_note': NOTA % (tiras, cm),
        'regulatory_basis': razon,
    }
    plan = Plan.with_context(active_test=False).search([('code', '=', code)], limit=1)
    if plan:
        plan.write(vals)
        print('[ok] %s actualizado (id %s)' % (code, plan.id))
    else:
        plan = Plan.create(vals)
        print('[ok] %s creado (id %s)' % (code, plan.id))
    print('     %s tiras = %s cm   %d productos%s' % (
        tiras, cm, len(prods), '   FALTAN: %s' % faltan if faltan else ''))
    print('     %s' % ' '.join(sorted(prods.mapped('default_code'))))

print('\n=== prueba: que cantidad saldria para un lote de 30 cm de cada hoja ===')
for c in TRES + DOS:
    p = Prod.search([('default_code', '=', c)], limit=1)
    if not p:
        continue
    pl = Plan.find_applicable_plan(p, 30.0, 'in_process')
    qty = pl.compute_sample_qty(30.0) if pl else 0.0
    print('   %-9s proceso -> %-14s %s cm (%s tiras)' % (
        c, pl.code or 'SIN PLAN', qty, int(round(qty / 0.3)) if qty else 0))
p = Prod.search([('default_code', '=', 'SPHMC56')], limit=1)
if p:
    pl = Plan.find_applicable_plan(p, 30.0, 'receipt')
    print('   %-9s recepcion -> %-12s %s cm  (hoja comprada: sigue con AQL, sin cambio)' % (
        'SPHMC56', pl.code or 'SIN PLAN', pl.compute_sample_qty(30.0) if pl else 0.0))
env.cr.commit()

# ---------------------------------------------------------------------------
# El operador no lee planes de muestreo: lee el nombre del paso en su orden.
# El paso se llamaba "Muestreo de tiras para analisis de Calidad - <prueba>" y no
# decia cuantas. Se le pone el numero al frente, conservando el nombre de la prueba.
# Solo afecta a las ordenes NUEVAS: la orden copia el nombre del paso al crearse.
# ---------------------------------------------------------------------------
print('\n=== el paso de la ruta ahora dice cuantas tiras ===')
for claves, cm in ((TRES, 0.9), (DOS, 0.6)):
    tiras = int(round(cm / 0.3))
    for c in claves:
        p = Prod.search([('default_code', '=', c)], limit=1)
        if not p:
            continue
        bom = env['mrp.bom'].sudo().search([('product_tmpl_id', '=', p.product_tmpl_id.id)], limit=1)
        if not bom:
            print('   %-9s sin BoM' % c); continue
        op = bom.operation_ids.filtered(lambda o: 'uestreo' in (o.name or ''))
        if not op:
            print('   %-9s sin paso de muestreo' % c); continue
        for o in op:
            if 'tiras (' in (o.name or ''):
                print('   %-9s ya estaba: %s' % (c, o.name)); continue
            sufijo = o.name.split(' - ', 1)[1] if ' - ' in o.name else ''
            nuevo = 'Muestreo para Calidad: %d tiras (%s cm)%s' % (
                tiras, cm, ' - %s' % sufijo if sufijo else '')
            o.write({'name': nuevo})
            # el nombre es traducible: si no se escribe es_MX, el usuario sigue viendo el viejo
            o.with_context(lang='es_MX').write({'name': nuevo})
            print('   %-9s %s' % (c, nuevo))
env.cr.commit()
