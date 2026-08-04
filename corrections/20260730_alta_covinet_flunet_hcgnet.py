# Completar/dar de alta COVINET (DIAM-029, /CNF), FLUNET (DMIAB01, /FLU) y HCG-NET
# (DMHCG02, /GCH creado), linea corta subtipo P. BoM 1pza + ruta 8 pasos + presentaciones
# con su empaque por presentacion. RS pendiente de capturar. Validado staging. Fernando 2026-07-30.
def prod(c): return env['product.product'].sudo().search([('default_code','=',c)],limit=1)
PRODS={
 'DIAM-029':{'ins':[('SPHMC01',0.4),('MPCAR01',1),('STDSC01',1),('STHIS01',1),('STTCT01',1),('MPBOL01',1)],
   'suf':'/CNF','sname':'Lote kit terminado - COVINET','etiq':'COVINET',
   'pres':[(2,[('COBHI01',1),('STBTR01',1),('MIMAN01',1)]),(5,[('MICAJ01',1),('STBTR01',1),('MIMAN01',1)]),(10,[('MICAJ05',1),('STBTR01',1),('MIMAN01',1)])]},
 'DMIAB01':{'ins':[('SPHMC14',0.4),('MPCAR14',1),('STDSC01',1),('MPBOL01',1),('STHIS01',1),('STTCT01',1)],
   'suf':'/FLU','sname':'Lote kit terminado - FLUNET','etiq':'FLUNET',
   'pres':[(5,[('MICAJ01',1),('STBTR01',1),('MIMAN01',1)]),(20,[('MICAJ06',1),('STBTR01',2),('MIMAN01',1)])]},
 'DMHCG02':{'ins':[('SPHMC21',0.4),('MPCAR21',1),('STGOT05',1),('STDSC01',1),('MPBOL01',1)],
   'suf':'/GCH','sname':'Lote kit terminado - HCG-NET','etiq':'HCG-NET',
   'pres':[(20,[('MICAJ01',1),('MIMAN01',1)])]},
}
ref=env['product.template'].sudo().search([('default_code','=','DMDMD01')],limit=1)
refbom=env['mrp.bom'].sudo().search([('product_tmpl_id','=',ref.id),('active','=',True)],limit=1)
F=env['mrp.routing.workcenter']._fields
Pres=env['amunet.packaging.presentation'].sudo(); PF=Pres._fields
for code,cfg in PRODS.items():
    tb=env['product.template'].sudo().search([('default_code','=',code)],limit=1)
    bom=env['mrp.bom'].sudo().search([('product_tmpl_id','=',tb.id)],limit=1)
    if not bom: bom=env['mrp.bom'].sudo().create({'product_tmpl_id':tb.id,'product_qty':1.0,'product_uom_id':tb.uom_id.id,'type':'normal','code':'BOM '+code})
    else: bom.write({'product_qty':1.0,'code':'BOM '+code,'product_uom_id':tb.uom_id.id})
    bom.bom_line_ids.unlink()
    for c,q in cfg['ins']:
        pr=prod(c); assert pr,'falta '+c
        env['mrp.bom.line'].sudo().create({'bom_id':bom.id,'product_id':pr.id,'product_qty':q,'product_uom_id':pr.uom_id.id})
    bom.operation_ids.unlink()
    for op in refbom.operation_ids.sorted('sequence'):
        v={'bom_id':bom.id,'name':op.name.split(' - ')[0]+' - '+cfg['etiq'],'workcenter_id':op.workcenter_id.id,'sequence':op.sequence,'time_cycle_manual':op.time_cycle_manual}
        if 'amunet_requires_supervision' in F: v['amunet_requires_supervision']=op.amunet_requires_supervision
        if 'amunet_requires_inspection' in F: v['amunet_requires_inspection']=op.amunet_requires_inspection
        env['mrp.routing.workcenter'].sudo().create(v)
    seq=env['ir.sequence'].sudo().search([('suffix','=',cfg['suf'])],limit=1)
    if not seq: seq=env['ir.sequence'].sudo().create({'name':cfg['sname'],'prefix':'%(month)s%(y)s/','suffix':cfg['suf'],'padding':2})
    tb.write({'mo_sequence_id':seq.id,'etiqueta_subtipo':'P'})
    for qty,comps in cfg['pres']:
        if Pres.search([('product_tmpl_id','=',tb.id),('package_qty','=',qty)],limit=1): continue
        cc=[(0,0,{'product_id':prod(c).id,'qty_per_box':q,'sequence':i}) for i,(c,q) in enumerate(comps)]
        v={'name':cfg['etiq']+' - Presentacion %d'%qty,'product_tmpl_id':tb.id,'product_id':tb.product_variant_id.id,'package_qty':qty,'is_authorized':True,'component_ids':cc}
        if 'authorization_source' in PF: v['authorization_source']='manual'
        Pres.create(v)
    print(code,cfg['etiq'],'| BOMq',bom.product_qty,'lin',len(bom.bom_line_ids),'ops',len(bom.operation_ids),'folio',seq.suffix,'subtipo',tb.etiqueta_subtipo,'pres',sorted(Pres.search([('product_tmpl_id','=',tb.id)]).mapped('package_qty')))
env.cr.commit()
print('ALTA3_OK')
