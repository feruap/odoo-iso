"""SPALMA14: alta, receta y ruta. Y el Hier 1 pasa de mg a ml.

Datos de Mery, 25-sep-2026:
  - A14 es igual en lamina y tamano de corte que A10: MPAFV01, 66 por lamina,
    0.3 x 30 cm.
  - Se pretrata con Hier 1 (MPAGE01), que **viene liquido** (por eso el cambio
    de unidad: estaba en mg y los microlitros son volumen).
  - Es la UNICA almohadilla que se corta ANTES de pretratar. Su ruta va al reves
    de las demas: corte -> pretratado -> secado. Las otras se sumergen, se secan
    y se cortan.
  - Pretratado: 2 ul por cm de almohadilla cortada.

Cuenta del Hier: cada almohadilla mide 30 cm -> 60 ul cada una -> 66 por lamina
= 3,960 ul = 3.96 ml por lamina.

NO usa la charola de 200 ml: eso aplica a las que se sumergen. Aqui el Hier se
aplica sobre la almohadilla ya cortada. El codigo de la charola solo toca
recetas PRETRATA-* cuyo componente este en volumen... OJO: esta receta ES
PRETRATA-* y su Hier ESTA en ml, asi que la charola SI le aplicaria. Se verifica
al final y se avisa si pasa.

Idempotente: busca todo por clave.
"""
PT   = env['product.template']
BOM  = env['mrp.bom']
Line = env['mrp.bom.line']
Op   = env['mrp.routing.workcenter']
WC   = env['mrp.workcenter']
ml   = env['uom.uom'].search([('name','=','ml')], limit=1)
uni  = env.ref('uom.product_uom_unit')
NOMBRE = 'Almohadilla A14 (Almohadilla intermedia pretratada con Hier 1) 0.3 x 30 cm'
assert ml, 'no existe la unidad ml'

# ---- 1) Hier 1: mg -> ml ----
hier = PT.search([('default_code','=','MPAGE01')], limit=1)
assert hier, 'no existe MPAGE01'
if hier.uom_id != ml:
    hier.write({'uom_id': ml.id})
    hier.message_post(body=(
        'Unidad corregida el 25-sep-2026: de <b>mg</b> a <b>ml</b>. El Hier 1 '
        'viene liquido (confirmado por Mery) y el pretratado de la almohadilla '
        'A14 se dosifica en microlitros, que es volumen.'))
    print('MPAGE01: mg -> ml')
else:
    print('MPAGE01: ya estaba en ml')

# ---- 2) alta de SPALMA14, calcada de A10 ----
molde = PT.search([('default_code','=','SPALMA10')], limit=1)
assert molde, 'no existe SPALMA10 para usar de molde'
a14 = PT.search([('default_code','=','SPALMA14')], limit=1)
if a14:
    print('SPALMA14: ya existe')
else:
    a14 = PT.with_context(amunet_alta_autorizada=True).create({
        'default_code': 'SPALMA14', 'name': NOMBRE,
        'type': molde.type, 'is_storable': molde.is_storable,
        'categ_id': molde.categ_id.id, 'uom_id': molde.uom_id.id,
        'tracking': molde.tracking,
        'use_expiration_date': True, 'expiration_time': 913,
        'qc_required': molde.qc_required,
        'amunet_req_quality_control': molde.amunet_req_quality_control,
        'amunet_etapa_ll': molde.amunet_etapa_ll,
        'route_ids': [(6, 0, molde.route_ids.ids)],
    })
    a14.with_context(lang='es_MX').write({'name': NOMBRE})
    print('SPALMA14: creado')

# ---- 3) receta ----
bom = BOM.search([('product_tmpl_id','=',a14.id)], limit=1)
if not bom:
    bom = BOM.create({
        'product_tmpl_id': a14.id, 'product_qty': 66.0,
        'product_uom_id': a14.uom_id.id, 'type': 'normal',
        'code': 'PRETRATA-SPALMA14',
        'consumption': BOM.search([('product_tmpl_id','=',molde.id)], limit=1).consumption,
    })
    print('receta PRETRATA-SPALMA14 creada, produce 66 por lamina')
for code, qty, uom in (('MPAFV01', 1.0, uni), ('STDSC01', 2.0, uni), ('MPAGE01', 3.96, ml)):
    p = env['product.product'].search([('default_code','=',code)], limit=1)
    assert p, 'falta %s' % code
    linea = bom.bom_line_ids.filtered(lambda l: l.product_id == p)
    if linea:
        linea.write({'product_qty': qty, 'product_uom_id': uom.id})
    else:
        Line.create({'bom_id': bom.id, 'product_id': p.id,
                     'product_qty': qty, 'product_uom_id': uom.id})
    print('   %-9s %6.2f %s' % (code, qty, uom.name))

# ---- 4) ruta INVERTIDA ----
almacen  = WC.search([('name','ilike','Almacén Materia Prima')], limit=1)
pretrat  = WC.search([('name','ilike','Lectura y Pretratamiento')], limit=1)
laminado = WC.search([('name','ilike','Laminado, Secado y Corte')], limit=1)
assert almacen and pretrat and laminado, 'faltan centros de trabajo'
ACTIVIDADES = [
    (5,  'Surtido de materiales - Almohadilla A14', almacen),
    (10, 'Corte a 0.3 cm - Almohadilla A14', laminado),
    (20, 'Pretratado: aplicar Hier 1, 2 ul por cm de almohadilla cortada - Almohadilla A14', pretrat),
    (30, 'Secado - Almohadilla A14', laminado),
    (40, 'Revision - Almohadilla A14', laminado),
    (50, 'Empaque con desecante (2 por lamina) - Almohadilla A14', laminado),
    (60, 'Entrega a almacen - Almohadilla A14', almacen),
]
print('ruta:')
for seq, nombre, wc in ACTIVIDADES:
    op = bom.operation_ids.filtered(lambda o: o.sequence == seq)
    if op:
        op.write({'name': nombre, 'workcenter_id': wc.id})
    else:
        Op.create({'bom_id': bom.id, 'name': nombre, 'sequence': seq,
                   'workcenter_id': wc.id, 'time_cycle_manual': 1})
    print('   %2d %-64s %s' % (seq, nombre[:64], wc.name))

a14.message_post(body=(
    'Alta y receta el 25-sep-2026, con los datos de Mery.<br/><br/>'
    '<b>Es la unica almohadilla que se corta ANTES de pretratar.</b> Ruta: '
    'corte, pretratado, secado. Las otras se sumergen, se secan y se cortan.'
    '<br/><br/>Pretratado: <b>2 ul por cm</b> de almohadilla cortada. Cada una '
    'mide 30 cm, asi que 60 ul cada una; por lamina de 66 son <b>3.96 ml</b> de '
    'Hier 1.<br/><br/>No se sumerge la lamina, asi que no aplica la charola de '
    '200 ml.'))
env.cr.commit()

# ---- 5) verificacion: la charola NO debe aplicarle ----
M = env['mrp.production']
rec = M.new({'product_id': a14.product_variant_id.id, 'bom_id': bom.id,
             'product_qty': 66.0, 'product_uom_id': a14.uom_id.id})
for v in rec._get_moves_raw_values():
    p = env['product.product'].browse(v['product_id'])
    if p.default_code == 'MPAGE01':
        if abs(v['product_uom_qty'] - 3.96) > 0.01:
            print('\n*** OJO: la charola le aplico. Pide %g ml en vez de 3.96 ***'
                  % v['product_uom_qty'])
        else:
            print('\nverificado: una orden de 1 lamina pide %g ml de Hier (correcto)'
                  % v['product_uom_qty'])
