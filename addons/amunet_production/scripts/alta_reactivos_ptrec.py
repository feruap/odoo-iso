# -*- coding: utf-8 -*-
"""Alta de los 10 reactivos reenvasados PTREC04-PTREC13.

Se compran a granel y se reenvasan aqui, por eso se producen. Se copia el patron
de los medios de cultivo (PTREC01-03): consumible, seguimiento por lote,
categoria Producto terminado / Reactivo, control de calidad requerido y la ruta
de 7 actividades de linea corta.

Diferencias con los medios de cultivo, indicadas por Mery el 21-sep-2026:
  - NO llevan desecante.
  - Cada producto tiene varias presentaciones en gramos. Como la cantidad de
    granel cambia con el tamano, se crea UN BoM POR PRESENTACION (Odoo admite
    varios BoM para el mismo producto). La clave sigue siendo una por producto.
  - El envase queda PENDIENTE: Mery lo va a indicar por presentacion. Por eso el
    BoM nace solo con el granel.

Idempotente.
"""
DATOS = [
 ('PTREC04','Tris-HCl','R04','MPREC04',[100,500]),
 ('PTREC05','Tris-base','R05','MPREC10',[100,500]),
 ('PTREC06','HEPES','R06','MPREC20',[250,500]),
 ('PTREC07','MOPS','R07','MPREC21',[100,500]),
 ('PTREC08','MES','R08','MPREC22',[100,500]),
 ('PTREC09','CHAPS','R09','MPREC23',[5,10,25]),
 ('PTREC10','Guanidine Hydrochloride','R10','MPREC24',[100,500]),
 ('PTREC11','TCEP-HCl','R11','MPREC27',[1,5,10]),
 ('PTREC12','IPTG','R12','MPREC25',[1,5,10]),
 ('PTREC13','DTT','R13','MPREC26',[1,5]),
]
PT=env['product.template'].sudo(); Bom=env['mrp.bom'].sudo()
modelo=PT.search([('default_code','=','PTREC01')],limit=1)
bmod=Bom.search([('product_tmpl_id','=',modelo.id),('active','=',True)],limit=1)
assert modelo and bmod, 'no se encontro el modelo PTREC01'
uom_u=modelo.uom_id

creados=0; boms=0
for clave, nombre, ref, granel, presentaciones in DATOS:
    g=PT.search([('default_code','=',granel)],limit=1)
    assert g, 'no existe el granel %s' % granel
    p=PT.search([('default_code','=',clave)],limit=1)
    vals={'name':nombre,'default_code':clave,'type':modelo.type,
          'categ_id':modelo.categ_id.id,'uom_id':uom_u.id,'tracking':'lot',
          'sale_ok':False,'purchase_ok':True}   # sale_ok se activa al final:
          # amunet_distribucion impide que un producto VENDIBLE sin BoM quede en
          # la categoria 'Producto terminado'. Se crea, se le carga el BoM y
          # entonces se marca vendible.
    for f in ('is_storable','qc_required'):
        if f in modelo._fields: vals[f]=modelo[f]
    if not p:
        p=PT.with_context(amunet_alta_autorizada=True).create(vals); creados+=1
        print('CREADO   %-9s %s' % (clave, nombre))
    else:
        p.with_context(amunet_alta_autorizada=True).write(vals)
        print('EXISTIA  %-9s %s (actualizado)' % (clave, nombre))
    # un BoM por presentacion: cambia la cantidad de granel
    for gramos in presentaciones:
        code='REENVASE-%s-%sg' % (clave, gramos)
        b=Bom.search([('product_tmpl_id','=',p.id),('code','=',code)],limit=1)
        if not b:
            b=Bom.sudo().create({'product_tmpl_id':p.id,'product_qty':1.0,
                                 'product_uom_id':uom_u.id,'type':'normal','code':code})
            boms+=1
        b.bom_line_ids.unlink()
        env['mrp.bom.line'].sudo().create({
            'bom_id':b.id,'product_id':g.product_variant_id.id,
            'product_qty':float(gramos),'product_uom_id':g.uom_id.id,'sequence':1})
        # ruta: las 7 actividades del modelo, renombradas y sin mencion al desecante
        b.operation_ids.unlink()
        for o in bmod.operation_ids.sorted('sequence'):
            n=(o.name or '')
            n=n.split(' - ')[0] if ' - ' in n else n
            n=n.replace('Ingreso de reactivo y desecante en empaque primario',
                        'Ingreso de reactivo en empaque primario')
            env['mrp.routing.workcenter'].sudo().create({
                'bom_id':b.id,'name':'%s - %s %s g' % (n, nombre, gramos),
                'workcenter_id':o.workcenter_id.id,'sequence':o.sequence,
                'time_cycle_manual':o.time_cycle_manual})
# ya con BoM cargado, se marcan vendibles
for clave, nombre, ref, granel, presentaciones in DATOS:
    pp=PT.search([('default_code','=',clave)],limit=1)
    if pp and not pp.sale_ok:
        pp.with_context(amunet_alta_autorizada=True).write({'sale_ok':True})
print('--- productos creados: %d   BoM creados: %d ---' % (creados, boms))
env.cr.commit()
