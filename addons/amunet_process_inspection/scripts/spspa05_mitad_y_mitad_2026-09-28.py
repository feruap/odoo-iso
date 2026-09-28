"""SPSPA05: mitad y mitad de las dos soluciones al 5%. Y alta de SPSPV01.

Como se hace en el dia, dicho por Mery el 28-sep-2026: se unen **500 ml de
Solucion de PVP al 5% y 500 ml de Solucion Hidroxido de Sodio al 5%**. Nada de
pesar los dos reactivos en el mismo vaso.

OJO CON EL NOMBRE: al mezclar mitad y mitad, la concentracion real de cada
reactivo queda en **2.5%**, no en 5%. El nombre se conserva por decision de
Mery: se refiere a las soluciones de origen, no a la mezcla final.
**NO RENOMBRAR.**

Caducidad: **3 meses** (90 dias), confirmado por Mery.

El documento controlado 'Solucion de PVP 5% + NaOH 5%.docx' dice otra cosa
(50 g de cada reactivo disueltos en agua) y Mery confirmo que **no representa
lo que se hace en el dia**. Ese documento trae ademas la clave equivocada: dice
SPSHS02, que es el hidroxido al 20%. Corregirlo le toca a Documentacion.

La cadena completa queda asi:

    MPREC11 PVP  polvo  -- 50 g/L -->  SPSPV01  PVP al 5%          \\
    MPREC09 NaOH polvo  -- 50 g/L -->  SPSHS03  Hidroxido al 5%    /  500 + 500 ml
                                            v
                                       SPSPA05  (1 L)
                                            v
                                       SPALMA09 (A9) -- 50 ml por lamina

Idempotente: busca todo por clave.
"""
PT   = env['product.template']
BOM  = env['mrp.bom']
Line = env['mrp.bom.line']
g  = env['uom.uom'].search([('name','=','g')], limit=1)
ml = env['uom.uom'].search([('name','=','ml')], limit=1)
L  = env['uom.uom'].search([('name','=','L')], limit=1)
assert g and ml and L, 'faltan unidades g / ml / L'
NOMBRE_PVP = 'Solución de PVP al 5%'
faltantes = []

# ---- 1) alta de SPSPV01, calcada de SPSHS03 ----
molde = PT.search([('default_code','=','SPSHS03')], limit=1)
if not molde:
    faltantes.append('SPSHS03 (molde para SPSPV01)')
pvp = PT.search([('default_code','=','SPSPV01')], limit=1)
if pvp:
    print('SPSPV01: ya existe')
elif molde:
    pvp = PT.with_context(amunet_alta_autorizada=True).create({
        'default_code': 'SPSPV01', 'name': NOMBRE_PVP,
        'type': molde.type, 'is_storable': molde.is_storable,
        'categ_id': molde.categ_id.id, 'uom_id': molde.uom_id.id,
        'tracking': molde.tracking,
        'use_expiration_date': molde.use_expiration_date,
        'qc_required': molde.qc_required,
        'amunet_req_quality_control': molde.amunet_req_quality_control,
        'route_ids': [(6, 0, molde.route_ids.ids)],
    })
    pvp.with_context(lang='es_MX').write({'name': NOMBRE_PVP})
    pvp.message_post(body=(
        'Alta el 28-sep-2026, autorizada por Mery. Por litro: <b>50 g de PVP '
        '(MPREC11)</b> en agua tridestilada, el mismo patron que la Solucion '
        'Hidroxido de Sodio al 5%.<br/><br/>Existe porque SPSPA05 se prepara '
        'uniendo mitad de esta y mitad de la de hidroxido, no pesando los '
        'reactivos en el mismo vaso.'))
    print('SPSPV01: creado')

# receta de SPSPV01: 50 g de PVP + el agua que lleve su molde
if pvp:
    bom_pvp = BOM.search([('product_tmpl_id','=',pvp.id)], limit=1)
    if not bom_pvp:
        bom_pvp = BOM.create({'product_tmpl_id': pvp.id, 'product_qty': 1.0,
                              'product_uom_id': L.id, 'type': 'normal',
                              'consumption': 'warning'})
    mb = BOM.search([('product_tmpl_id','=',molde.id)], limit=1) if molde else None
    agua_qty, agua_uom = 0.05, None
    if mb:
        for l in mb.bom_line_ids:
            if l.product_id.default_code == 'MPATR01':
                agua_qty, agua_uom = l.product_qty, l.product_uom_id
    for code, qty, uom in (('MPREC11', 50.0, g), ('MPATR01', agua_qty, agua_uom)):
        p = env['product.product'].search([('default_code','=',code)], limit=1)
        if not p or not uom:
            faltantes.append(code); continue
        linea = bom_pvp.bom_line_ids.filtered(lambda x: x.product_id == p)
        if linea:
            linea.write({'product_qty': qty, 'product_uom_id': uom.id})
        else:
            Line.create({'bom_id': bom_pvp.id, 'product_id': p.id,
                         'product_qty': qty, 'product_uom_id': uom.id})
        print('   SPSPV01 <- %-9s %8.2f %s' % (code, qty, uom.name))

# ---- 2) SPSPA05: mitad y mitad ----
t = PT.search([('default_code','=','SPSPA05')], limit=1)
if not t:
    faltantes.append('SPSPA05')
else:
    bom = BOM.search([('product_tmpl_id','=',t.id)], limit=1)
    if not bom:
        faltantes.append('receta de SPSPA05')
    else:
        NUEVA = {'SPSPV01': 500.0, 'SPSHS03': 500.0}
        for l in bom.bom_line_ids:
            if l.product_id.default_code not in NUEVA:
                print('   SPSPA05: retirado %s' % l.product_id.default_code)
                l.unlink()
        for code, qty in NUEVA.items():
            p = env['product.product'].search([('default_code','=',code)], limit=1)
            if not p:
                faltantes.append(code); continue
            linea = bom.bom_line_ids.filtered(lambda x: x.product_id == p)
            if linea:
                linea.write({'product_qty': qty, 'product_uom_id': ml.id})
            else:
                Line.create({'bom_id': bom.id, 'product_id': p.id,
                             'product_qty': qty, 'product_uom_id': ml.id})
            print('   SPSPA05 <- %-9s %8.2f ml' % (code, qty))
        # caducidad 3 meses
        if t.expiration_time != 90:
            t.write({'use_expiration_date': True, 'expiration_time': 90})
            print('   SPSPA05: caducidad 3 meses (90 dias)')
        t.message_post(body=(
            '<b>Formula corregida el 28-sep-2026</b>, con lo que Mery indico que '
            'se hace en el dia: <b>500 ml de Solucion de PVP al 5% (SPSPV01)</b> '
            'mas <b>500 ml de Solucion Hidroxido de Sodio al 5% (SPSHS03)</b>. '
            'Mitad y mitad. Caducidad <b>3 meses</b>.'
            '<br/><br/><b>OJO CON EL NOMBRE:</b> al mezclar mitad y mitad la '
            'concentracion real de cada reactivo queda en <b>2.5%</b>, no en 5%. '
            'El nombre se conserva por decision de Mery: se refiere a las '
            'soluciones de origen. <b>No renombrar.</b>'
            '<br/><br/>El documento controlado dice 50 g de cada reactivo en '
            'agua, y no representa lo que se hace. Tambien trae la clave '
            'equivocada (SPSHS02, que es el hidroxido al 20%).'))

if faltantes:
    print('\nFALTANTES, no se guardo nada: %s' % ', '.join(faltantes))
else:
    env.cr.commit()
    print('\nOK: guardado.')
