# Alta de Salmonella typhi (DMSAT01) y Shigella flexneri (DMSGF01), linea corta heces.
# BoM 1 pza con 6 insumos (vial STBPR03 va en BoM = material por prueba) + ruta 8 pasos.
# Folios /SAL (existe) y /SFA (se crea). Subtipo S. Presentaciones 5 y 20 (Caja MICAJ01 + Instructivo).
# Validado en staging. Autorizado por Fernando 2026-07-29.
def prod(code): return env['product.product'].sudo().search([('default_code','=',code)],limit=1)
CFG = {
 'DMSAT01': {'insumos':[('SPHMC45',0.4),('MPCAR45',1),('STBPR03',1),('STGOT05',1),('STDSC01',1),('MPBOL01',1)],
             'suffix':'/SAL','seqname':'Lote kit terminado - Salmonella typhi','etiq':'SALMONELLA TYPHI'},
 'DMSGF01': {'insumos':[('SPHMC60',0.4),('MPCAR60',1),('STBPR03',1),('STGOT05',1),('STDSC01',1),('MPBOL01',1)],
             'suffix':'/SFA','seqname':'Lote kit terminado - Shigella flexneri','etiq':'SHIGELLA FLEXNERI'},
}
PRES=[5,20]; EMPAQUE=['MICAJ01','MIMAN01']
ref=env['product.template'].sudo().search([('default_code','=','DMDMD01')],limit=1)
refbom=env['mrp.bom'].sudo().search([('product_tmpl_id','=',ref.id),('active','=',True)],limit=1)
F=env['mrp.routing.workcenter']._fields
Pres=env['amunet.packaging.presentation'].sudo(); PF=Pres._fields
for code,cfg in CFG.items():
    tb=env['product.template'].sudo().search([('default_code','=',code)],limit=1)
    assert tb, code+' no existe'
    bom=env['mrp.bom'].sudo().search([('product_tmpl_id','=',tb.id)],limit=1)
    if not bom:
        bom=env['mrp.bom'].sudo().create({'product_tmpl_id':tb.id,'product_qty':1.0,'product_uom_id':tb.uom_id.id,'type':'normal','code':'BOM '+code})
    else:
        bom.write({'product_qty':1.0,'code':'BOM '+code,'product_uom_id':tb.uom_id.id})
    bom.bom_line_ids.unlink()
    for c,q in cfg['insumos']:
        pr=prod(c); assert pr,'falta '+c
        env['mrp.bom.line'].sudo().create({'bom_id':bom.id,'product_id':pr.id,'product_qty':q,'product_uom_id':pr.uom_id.id})
    bom.operation_ids.unlink()
    nom=tb.name.replace('Prueba rápida de ','') if tb.name else code
    for op in refbom.operation_ids.sorted('sequence'):
        v={'bom_id':bom.id,'name':op.name.split(' - ')[0]+' - '+cfg['etiq'],'workcenter_id':op.workcenter_id.id,'sequence':op.sequence,'time_cycle_manual':op.time_cycle_manual}
        if 'amunet_requires_supervision' in F: v['amunet_requires_supervision']=op.amunet_requires_supervision
        if 'amunet_requires_inspection' in F: v['amunet_requires_inspection']=op.amunet_requires_inspection
        env['mrp.routing.workcenter'].sudo().create(v)
    seq=env['ir.sequence'].sudo().search([('suffix','=',cfg['suffix'])],limit=1)
    if not seq:
        seq=env['ir.sequence'].sudo().create({'name':cfg['seqname'],'prefix':'%(month)s%(y)s/','suffix':cfg['suffix'],'padding':2})
    tb.write({'mo_sequence_id':seq.id,'etiqueta_subtipo':'S','nombre_etiqueta':cfg['etiq']})
    for qty in PRES:
        if Pres.search([('product_tmpl_id','=',tb.id),('package_qty','=',qty)],limit=1): continue
        comps=[(0,0,{'product_id':prod(c).id,'qty_per_box':1.0,'sequence':i}) for i,c in enumerate(EMPAQUE)]
        v={'name':cfg['etiq']+' - Presentacion %d'%qty,'product_tmpl_id':tb.id,'product_id':tb.product_variant_id.id,'package_qty':qty,'is_authorized':True,'component_ids':comps}
        if 'authorization_source' in PF: v['authorization_source']='manual'
        Pres.create(v)
    print(code,'BOM_qty',bom.product_qty,'lineas',len(bom.bom_line_ids),'ops',len(bom.operation_ids),'seq',seq.suffix,'subtipo',tb.etiqueta_subtipo,'pres',sorted(Pres.search([('product_tmpl_id','=',tb.id)]).mapped('package_qty')))
env.cr.commit()
print('ALTA_HECES_OK')
