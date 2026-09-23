# -*- coding: utf-8 -*-
"""Despliegue de CONJUGADOS a produccion (datos).

Corre DESPUES de que el codigo este desplegado. Idempotente: se puede volver a
correr sin duplicar nada. Todo se busca por clave, nunca por id.

Hace, en este orden:
  1. unidad ug (los anticuerpos se manejan en mg; 37.5 ug es ilegible en mg)
  2. los 29 productos SPCDE
  3. etapa de linea larga de conjugados y soluciones (sin esto el campo
     Producto de una orden de solucion sale VACIO)
  4. parametros de receta de los 19 con datos
  5. las 19 recetas, con su anticuerpo en ug
"""
from odoo import Command

P = env['product.product']
T = env['product.template']
Uom = env['uom.uom']
Bom = env['mrp.bom']
resumen = []

def clave(c):
    return P.search([('default_code', '=', c)], limit=1)

# ---------------------------------------------------------------- 1. unidad ug
ug = Uom.search([('name', '=', 'µg')], limit=1)
if not ug:
    mg = Uom.search([('name', '=', 'mg')], limit=1)
    ug = Uom.create({'name': 'µg', 'relative_factor': 0.001, 'relative_uom_id': mg.id})
    resumen.append('unidad µg creada (id %s)' % ug.id)
else:
    resumen.append('unidad µg ya existia (id %s)' % ug.id)
ml = Uom.search([('name', '=', 'ml')], limit=1)

# ------------------------------------------------------------- 2. los productos
CONJUGADOS = [
    ('SPCDE01', 'Solución de conjugado anti-Influenza A'),
    ('SPCDE02', 'Solución de conjugado anti-Influenza B'),
    ('SPCDE03', 'Solución de conjugado anti-fluoresceína (anti-FIT)'),
    ('SPCDE04', 'Solución de conjugado anti-Mioglobina'),
    ('SPCDE05', 'Solución de conjugado anti-CK-MB'),
    ('SPCDE06', 'Solución de conjugado anti-cTnI'),
    ('SPCDE07', 'Solución de conjugado anti-Chlamydia trachomatis'),
    ('SPCDE08', 'Solución de conjugado anti-proteína N SARS-CoV-2'),
    ('SPCDE09', 'Solución de conjugado Antígeno de Dengue'),
    ('SPCDE10', 'Solución de conjugado anti-NS1 del Dengue'),
    ('SPCDE11', 'Solución de conjugado anti-ferritina'),
    ('SPCDE12', 'Solución de conjugado anti-hCG'),
    ('SPCDE13', 'Solución de conjugado anti-hemoglobina glicada'),
    ('SPCDE14', 'Solución de conjugado anti-PSA'),
    ('SPCDE15', 'Solución de conjugado anti-rotavirus'),
    ('SPCDE16', 'Solución de conjugado anti-adenovirus'),
    ('SPCDE17', 'Solución de conjugado anti-RSV'),
    ('SPCDE18', 'Solución de conjugado anti-25(OH)D'),
    ('SPCDE19', 'Solución de conjugado anti-TSH'),
    ('SPCDE20', 'Solución de conjugado anti-Strep A'),
    ('SPCDE21', 'Solución de conjugado control de detección'),
    ('SPCDE22', 'Solución de conjugado Sífilis'),
    ('SPCDE23', 'Solución de conjugado anti-Dímero D'),
    ('SPCDE24', 'Solución de conjugado anti-Salmonella typhi'),
    ('SPCDE25', 'Solución de conjugado anti-NT-proBNP'),
    ('SPCDE26', 'Solución de conjugado p24 VIH 1'),
    ('SPCDE27', 'Solución de conjugado anti-CA125'),
    ('SPCDE28', 'Solución de conjugado anti-CA 15 3'),
    ('SPCDE29', 'Solución de conjugado control Sífilis'),
]
categ = env['product.category'].search(
    [('complete_name', '=', 'Semiprocesado / Soluciones de trabajo')], limit=1)
if not categ:
    raise Exception('No existe la categoria Semiprocesado / Soluciones de trabajo')
manu = env['stock.route'].search([('name', 'ilike', 'Manufacture')], limit=1)

nuevos = actualizados = 0
for cod, nombre in CONJUGADOS:
    t = T.search([('default_code', '=', cod)], limit=1)
    vals = {
        'type': 'consu', 'is_storable': True, 'categ_id': categ.id,
        'uom_id': ml.id, 'tracking': 'lot',
        'purchase_ok': False, 'sale_ok': False,
        'amunet_expiration_text': '15 Dias',
        'amunet_es_conjugado': True, 'amunet_etapa_ll': 'conjugados',
        'amunet_req_aforar': False,
        'qc_required': False, 'amunet_req_quality_control': False,
    }
    if manu:
        vals['route_ids'] = [Command.set([manu.id])]
    if t:
        t.write(vals)
        actualizados += 1
    else:
        vals.update({'default_code': cod, 'name': nombre})
        t = T.with_context(amunet_alta_autorizada=True).create(vals)
        nuevos += 1
    for lang in ('en_US', 'es_MX'):
        t.with_context(lang=lang).write({'name': nombre})
resumen.append('productos: %s nuevos, %s actualizados' % (nuevos, actualizados))

# ------------------------------------------- 3. etapa de linea larga (CRITICO)
conj = T.search([('amunet_es_conjugado', '=', True)])
conj.write({'amunet_etapa_ll': 'conjugados'})
sol = T.search([('categ_id.complete_name', 'ilike', 'soluc'),
                ('amunet_es_conjugado', '=', False)])
sol.write({'amunet_etapa_ll': 'soluciones'})
resumen.append('etapa: %s conjugados, %s soluciones' % (len(conj), len(sol)))

# ------------------------------------------------- 4. parametros de receta (19)
PARAMS = {
    'SPCDE01': ('7.5', 'cas', 2.0, 30, 9.0, 'estandar'),
    'SPCDE02': ('8.5', 'cas', 2.0, 30, 8.0, 'estandar'),
    'SPCDE03': ('8.5', 'cas', 2.0, 30, 10.0, 'estandar'),
    'SPCDE08': ('7.5', 'cas', 2.0, 30, 10.0, 'estandar'),
    'SPCDE09': ('7.5', 'cas', 2.0, 30, 10.0, 'estandar'),
    'SPCDE10': ('7.5', 'cas', 1.5, 30, 12.0, 'largo'),
    'SPCDE12': ('8.5', 'cas', 2.0, 30, 10.0, 'estandar'),
    'SPCDE13': ('7.5', 'cas', 2.0, 30, 10.0, 'estandar'),
    'SPCDE14': ('7.5', 'cas', 1.5, 15, 10.0, 'largo'),
    'SPCDE17': ('8.5', 'cas', 2.0, 30, 10.0, 'estandar'),
    'SPCDE18': ('7.5', 'cas', 2.0, 30, 12.4, 'estandar'),
    'SPCDE19': ('7.5', 'bsa', 1.5, 30, 10.0, 'largo'),
    'SPCDE20': ('7.5', 'cas', 2.0, 30, 10.0, 'estandar'),
    'SPCDE21': ('8.5', 'cb',  2.0, 30, 20.0, 'estandar'),
    'SPCDE22': ('7.5', 'bsa', 2.0, 30, 10.0, 'estandar'),
    'SPCDE23': ('7.5', 'cas', 2.0, 30, 10.0, 'estandar'),
    'SPCDE24': ('7.5', 'cas', 2.0, 30, 10.0, 'estandar'),
    'SPCDE26': ('7.5', 'cas', 2.0, 30, 10.0, 'estandar'),
    'SPCDE29': ('8.5', 'bsa', 2.0, 30, 10.0, 'estandar'),
}
for cod, (ph, bloq, hc, mb, do, proc) in PARAMS.items():
    t = T.search([('default_code', '=', cod)], limit=1)
    if t:
        t.write({'amunet_conj_ph_sab': ph, 'amunet_conj_agente_bloqueo': bloq,
                 'amunet_conj_horas_conjugacion': hc, 'amunet_conj_min_bloqueo': float(mb),
                 'amunet_conj_do_objetivo': do, 'amunet_conj_proceso': proc,
                 'amunet_conj_vol_resuspension': 30.0})
resumen.append('parametros de receta: %s conjugados' % len(PARAMS))

# ------------------------------------------------------------ 5. las 19 recetas
SAB = {'7.5': 'SPSPC04', '8.5': 'SPSPC05'}
DIL = {'AD0': 'SPSDC01', 'AD1': 'SPSDC02'}
BSA = {'7.5': 'SPSPB01', '8.5': 'SPSPB02'}
# conjugado: (nps_mL, pH, bloqueo, diluyente, anticuerpo, ug/mL)
RECETAS = {
    'SPCDE01': (5, '7.5', 'cas', 'AD1', 'MPANT31', 7.5),
    'SPCDE02': (5, '8.5', 'cas', 'AD0', 'MPANT30', 5.0),
    'SPCDE03': (3, '8.5', 'cas', 'AD1', 'MPANT34', 7.5),
    'SPCDE08': (5, '7.5', 'cas', 'AD1', 'MPANT05', 8.0),
    'SPCDE09': (5, '7.5', 'cas', 'AD1', 'MPAG08', 10.0),
    'SPCDE10': (5, '7.5', 'cas', 'AD1', 'MPANT32', 10.0),
    'SPCDE12': (5, '8.5', 'cas', 'AD0', 'MPANT10', 10.0),
    'SPCDE13': (5, '7.5', 'cas', 'AD1', 'MPANT13', 15.0),
    'SPCDE14': (5, '7.5', 'cas', 'AD1', 'MPANT36', 15.0),
    'SPCDE17': (5, '8.5', 'cas', 'AD1', 'MPANT38', 10.0),
    'SPCDE18': (5, '7.5', 'cas', 'AD1', 'MPANT16', 10.0),
    'SPCDE19': (5, '7.5', 'bsa', 'AD0', 'MPANT56', 15.0),
    'SPCDE20': (5, '7.5', 'cas', 'AD1', 'MPANT67', 5.0),
    'SPCDE21': (5, '8.5', 'cb',  'AD0', 'MPANT06', 10.0),
    'SPCDE22': (5, '7.5', 'bsa', 'AD0', 'MPAG10', 10.0),
    'SPCDE23': (5, '7.5', 'cas', 'AD1', 'MPANT54', 5.0),
    'SPCDE24': (5, '7.5', 'cas', 'AD1', 'MPANT50', 5.0),
    'SPCDE26': (5, '7.5', 'cas', 'AD1', 'MPANT40', 15.0),
    'SPCDE29': (5, '8.5', 'bsa', 'AD0', 'MPANT48', 10.0),
}
creados = existentes = 0
faltantes = []
for cod, (nps, ph, bloq, dil, ac, conc) in sorted(RECETAS.items()):
    prod = clave(cod)
    if not prod:
        faltantes.append('producto %s' % cod); continue
    if Bom.search([('product_tmpl_id', '=', prod.product_tmpl_id.id), ('active', '=', True)]):
        existentes += 1; continue
    lineas = []
    def linea(c, qty, uom):
        p = clave(c)
        if not p:
            faltantes.append('insumo %s (receta %s)' % (c, cod)); return None
        return Command.create({'product_id': p.id, 'product_qty': qty, 'product_uom_id': uom.id})
    for c, q in ((('SPNPS01'), float(nps)), (SAB[ph], float(nps))):
        l = linea(c, q, ml)
        if l: lineas.append(l)
    if bloq == 'cas':
        l = linea('SPSPB03', float(nps), ml)
        if l: lineas.append(l)
    elif bloq == 'bsa':
        l = linea(BSA[ph], float(nps), ml)
        if l: lineas.append(l)
    else:  # caseina y BSA, mitad y mitad
        for c in ('SPSPB03', BSA[ph]):
            l = linea(c, nps / 2.0, ml)
            if l: lineas.append(l)
    l = linea(DIL[dil], round(nps * 0.1, 4), ml)
    if l: lineas.append(l)
    l = linea(ac, conc * nps, ug)          # anticuerpo en CANTIDAD
    if l: lineas.append(l)
    Bom.create({
        'product_tmpl_id': prod.product_tmpl_id.id,
        'product_qty': round(nps * 0.1, 4), 'product_uom_id': ml.id,
        'type': 'normal', 'company_id': env.company.id,
        'bom_line_ids': lineas,
    })
    creados += 1
resumen.append('recetas: %s creadas, %s ya existian' % (creados, existentes))
if faltantes:
    resumen.append('FALTANTES: %s' % ', '.join(sorted(set(faltantes))))

env.cr.commit()
print('\n'.join('  ' + r for r in resumen))
print('COMMIT OK')
