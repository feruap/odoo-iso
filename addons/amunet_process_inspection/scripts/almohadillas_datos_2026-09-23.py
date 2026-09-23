"""Datos de las almohadillas SPALMA que acompanan a la version 19.0.4.4.0.

El codigo (charola de 200 ml, aviso de multiplo, caducidad heredada) viaja en
el modulo. Estos son los datos que el merge NO trae y hay que cargar aparte:

  1. Caducidad: 2.5 anos (913 dias) en las 6 pretratadas; las 7 de corte sin
     plazo propio, porque heredan la del lote de lamina que consumen.
  2. SPSPA04 (solucion de orina, ya dada de alta) conectada a la receta de la
     A8 a 60 ml/lamina. Estaba de alta pero nadie la habia conectado.
  3. SPSPA05 nueva: solucion de pretratamiento para la almohadilla intermedia
     (PVP + NaOH 5%), conectada a la A9 a 50 ml/lamina.

Los ml van con la LAMINA, no con el corte: MPAFV01 -> 50, MPAFV02 -> 60.

PENDIENTE al momento de escribir esto: SPSPA05 no tiene receta propia. El
producto existe y las ordenes de A9 ya lo piden, pero falta su formulacion
por litro (PVP MPREC11 + NaOH MPREC09). Mery la dara.

Idempotente: busca todo por clave, no por id. Correrlo dos veces no duplica.
Solicitado por Mery, 23-sep-2026.
"""

PT   = env['product.template']
BOM  = env['mrp.bom']
Line = env['mrp.bom.line']
ml   = env['uom.uom'].search([('name', '=', 'ml')], limit=1)
assert ml, 'No existe la unidad ml'

PRETRATADAS = ['SPALMA01', 'SPALMA03', 'SPALMA04', 'SPALMA06', 'SPALMA08', 'SPALMA09']
CORTE = ['SPALMA02', 'SPALMA05', 'SPALMA07', 'SPALMA10',
         'SPALMA11', 'SPALMA12', 'SPALMA13']
NOMBRE_05 = 'Solución de pretratamiento para almohadilla intermedia (PVP + NaOH 5%)'

faltantes = []

# --- 1. Caducidad -----------------------------------------------------------
print('--- caducidad ---')
for code in PRETRATADAS:
    p = PT.search([('default_code', '=', code)], limit=1)
    if not p:
        faltantes.append(code)
        continue
    p.write({'use_expiration_date': True, 'expiration_time': 913})
    print('  %s -> 913 dias (2.5 anos)' % code)
for code in CORTE:
    p = PT.search([('default_code', '=', code)], limit=1)
    if not p:
        faltantes.append(code)
        continue
    p.write({'use_expiration_date': True, 'expiration_time': 0})
    print('  %s -> hereda del insumo' % code)

# --- 2. SPSPA05: alta -------------------------------------------------------
print('--- SPSPA05 ---')
sp05 = PT.search([('default_code', '=', 'SPSPA05')], limit=1)
if sp05:
    print('  ya existe')
else:
    molde = PT.search([('default_code', '=', 'SPSPA04')], limit=1)
    if not molde:
        faltantes.append('SPSPA04 (molde para dar de alta SPSPA05)')
    else:
        sp05 = PT.with_context(amunet_alta_autorizada=True).create({
            'default_code': 'SPSPA05',
            'name': NOMBRE_05,
            'type': molde.type,
            'is_storable': molde.is_storable,
            'categ_id': molde.categ_id.id,
            'uom_id': molde.uom_id.id,
            'tracking': molde.tracking,
            'use_expiration_date': molde.use_expiration_date,
            'qc_required': molde.qc_required,
            'amunet_req_quality_control': molde.amunet_req_quality_control,
            'route_ids': [(6, 0, molde.route_ids.ids)],
        })
        # el nombre es traducible: sin es_MX el usuario sigue viendo el ingles
        sp05.with_context(lang='es_MX').write({'name': NOMBRE_05})
        print('  creado: %s' % sp05.name)

# --- 3. Conectar las soluciones a sus recetas -------------------------------
print('--- recetas ---')
for almo, sol_code, mls in (('SPALMA08', 'SPSPA04', 60.0),
                            ('SPALMA09', 'SPSPA05', 50.0)):
    bom = BOM.search([('code', '=', 'PRETRATA-' + almo)], limit=1)
    sol = env['product.product'].search([('default_code', '=', sol_code)], limit=1)
    if not bom or not sol:
        faltantes.append('receta PRETRATA-%s o producto %s' % (almo, sol_code))
        continue
    linea = bom.bom_line_ids.filtered(lambda l: l.product_id == sol)
    if linea:
        linea.write({'product_qty': mls, 'product_uom_id': ml.id})
        print('  %s: %s actualizada a %s ml/lamina' % (almo, sol_code, int(mls)))
    else:
        Line.create({'bom_id': bom.id, 'product_id': sol.id,
                     'product_qty': mls, 'product_uom_id': ml.id})
        print('  %s: %s conectada a %s ml/lamina' % (almo, sol_code, int(mls)))

if faltantes:
    print('\nFALTANTES (revisar antes de dar por bueno):')
    for f in faltantes:
        print('   ', f)
else:
    env.cr.commit()
    print('\nOK: cambios guardados.')
