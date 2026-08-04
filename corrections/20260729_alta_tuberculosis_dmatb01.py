# Completa el alta de TUBERCULOSIS (DMATB01) en produccion: BoM a 1 pieza con
# los 5 insumos de la ficha + ruta estandar 8 pasos (copiada de DMDMD01),
# secuencia de folio /TUB, subtipo de etiqueta S, y presentaciones 2/5/10/12/20
# con empaque (Caja MICAJ01 + Vial STBPR01 + Instructivo MIMAN01).
# Validado en staging (folio 0726/01/TUB, receta explota bien). Autorizado por Fernando 2026-07-29.
def prod(code):
    return env['product.product'].sudo().search([('default_code','=',code)], limit=1)
tb = env['product.template'].sudo().search([('default_code','=','DMATB01')], limit=1)
assert tb, 'DMATB01 no existe en prod'

# BoM (fijar o crear)
bom = env['mrp.bom'].sudo().search([('product_tmpl_id','=',tb.id)], limit=1)
if not bom:
    bom = env['mrp.bom'].sudo().create({'product_tmpl_id':tb.id,'product_qty':1.0,
        'product_uom_id':tb.uom_id.id,'type':'normal','code':'BOM Tuberculosis DMATB01'})
else:
    bom.write({'product_qty':1.0,'code':'BOM Tuberculosis DMATB01','product_uom_id':tb.uom_id.id})
bom.bom_line_ids.unlink()
for code,qty in [('SPHMC28',0.4),('MPCAR28',1.0),('STGOT04',1.0),('STDSC01',1.0),('MPBOL01',1.0)]:
    pr=prod(code); assert pr, 'falta insumo '+code
    env['mrp.bom.line'].sudo().create({'bom_id':bom.id,'product_id':pr.id,'product_qty':qty,'product_uom_id':pr.uom_id.id})

# Ruta: copiar de DMDMD01
ref=env['product.template'].sudo().search([('default_code','=','DMDMD01')],limit=1)
refbom=env['mrp.bom'].sudo().search([('product_tmpl_id','=',ref.id),('active','=',True)],limit=1)
assert refbom and len(refbom.operation_ids)==8, 'ruta de referencia DMDMD01 no valida'
bom.operation_ids.unlink()
F=env['mrp.routing.workcenter']._fields
for op in refbom.operation_ids.sorted('sequence'):
    vals={'bom_id':bom.id,'name':op.name.replace('DIMERO D','TUBERCULOSIS').replace('DIMERO-D','TUBERCULOSIS'),
          'workcenter_id':op.workcenter_id.id,'sequence':op.sequence,'time_cycle_manual':op.time_cycle_manual}
    if 'amunet_requires_supervision' in F: vals['amunet_requires_supervision']=op.amunet_requires_supervision
    if 'amunet_requires_inspection' in F: vals['amunet_requires_inspection']=op.amunet_requires_inspection
    env['mrp.routing.workcenter'].sudo().create(vals)

# Secuencia de folio /TUB (buscar; crear si falta)
seq=env['ir.sequence'].sudo().search([('suffix','=','/TUB')],limit=1)
if not seq:
    seq=env['ir.sequence'].sudo().create({'name':'Lote kit terminado - Tuberculosis',
        'prefix':'%(month)s%(y)s/','suffix':'/TUB','padding':2})
tb.write({'mo_sequence_id':seq.id,'etiqueta_subtipo':'S'})

# Presentaciones 2/5/10/12/20 con empaque
Pres=env['amunet.packaging.presentation'].sudo(); PF=Pres._fields
for qty in [2,5,10,12,20]:
    if Pres.search([('product_tmpl_id','=',tb.id),('package_qty','=',qty)],limit=1): continue
    comps=[(0,0,{'product_id':prod(c).id,'qty_per_box':1.0,'sequence':i}) for i,c in enumerate(['MICAJ01','STBPR01','MIMAN01'])]
    v={'name':'TUBERCULOSIS - Presentacion %d'%qty,'product_tmpl_id':tb.id,'product_id':tb.product_variant_id.id,
       'package_qty':qty,'is_authorized':True,'component_ids':comps}
    if 'authorization_source' in PF: v['authorization_source']='manual'
    Pres.create(v)
env.cr.commit()

# Verificacion
bom=env['mrp.bom'].sudo().search([('product_tmpl_id','=',tb.id)],limit=1)
print('BOM qty:',bom.product_qty,'| lineas:',sorted([(l.product_id.default_code,l.product_qty) for l in bom.bom_line_ids]),'| ops:',len(bom.operation_ids))
print('mo_sequence:',tb.mo_sequence_id.name,'| subtipo:',tb.etiqueta_subtipo)
print('presentaciones:',sorted(Pres.search([('product_tmpl_id','=',tb.id)]).mapped('package_qty')))
print('LISTO')
