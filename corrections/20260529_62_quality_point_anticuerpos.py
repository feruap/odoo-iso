# Configurar amunet.quality.point para todos los anticuerpos/antigenos Fapon
# Aplica a recepciones de incoming en cualquier almacen
cat_anti = env['product.category'].search([('complete_name','=','Materia prima / Anticuerpo')], limit=1)
cat_antg = env['product.category'].search([('complete_name','=','Materia prima / Antigeno recombinante')], limit=1)
cat_aux  = env['product.category'].search([('complete_name','=','Materia prima / Reactivo auxiliar')], limit=1)
cats = [c for c in [cat_anti, cat_antg, cat_aux] if c]

products = env['product.product'].search([('categ_id','in',[c.id for c in cats])])
print(f"Productos Fapon (anticuerpo/antigeno/aux): {len(products)}")

# Quality point generico para todos los productos Fapon
qp_name = 'QC Recepcion Anticuerpos/Antigenos Fapon'
qp = env['amunet.quality.point'].search([('name','=',qp_name)], limit=1)
incoming_types = env['stock.picking.type'].search([('code','=','incoming'),('active','=',True)])

if not qp:
    qp_vals = {'name':qp_name,'active':True}
    # asignar productos
    if 'product_ids' in env['amunet.quality.point']._fields:
        qp_vals['product_ids'] = [(6,0,products.ids)]
    if 'picking_type_ids' in env['amunet.quality.point']._fields:
        qp_vals['picking_type_ids'] = [(6,0,incoming_types.ids)]
    qp = env['amunet.quality.point'].create(qp_vals)
    env.cr.commit()
    print(f"  CREADO quality_point id={qp.id} '{qp.name}'")
    print(f"     Productos: {len(products)}")
    print(f"     Picking types incoming: {incoming_types.mapped('display_name')}")
else:
    print(f"  YA OK quality_point id={qp.id}")
