# Idempotente: crea MPCAR72 (cassette combo resp), categoria Cartucho armado, STCAR_CR01 y su BoM
from datetime import date

cang = env['res.partner'].search([('name','ilike','Cangzhou ShengFeng')], limit=1)
usd = env.ref('base.USD')
unit = env.ref('uom.product_uom_unit')

# MPCAR72
mpcar72 = env['product.template'].search([('default_code','=','MPCAR72')], limit=1)
if not mpcar72:
    cat = env['product.category'].search([('complete_name','=','Materia prima / Cartucho')], limit=1)
    mpcar72 = env['product.template'].create({
        'default_code':'MPCAR72',
        'name':'Cartucho Combo Respiratorio (Multi-3 COV/FLU/RSV)',
        'type':'consu','is_storable':True,'sale_ok':False,'purchase_ok':True,
        'uom_id':unit.id, 'categ_id':cat.id if cat else 1,
    })
    env.cr.commit()
    print(f"  CREADO MPCAR72 id={mpcar72.id}")
else:
    print(f"  YA OK MPCAR72 id={mpcar72.id}")

# supplierinfo MPCAR72 <- Cangzhou K067 $0.05
if cang:
    dup = env['product.supplierinfo'].search([
        ('product_tmpl_id','=',mpcar72.id),('partner_id','=',cang.id),('product_code','=','K067')
    ], limit=1)
    if not dup:
        env['product.supplierinfo'].create({
            'product_tmpl_id':mpcar72.id,'partner_id':cang.id,
            'product_code':'K067',
            'product_name':'Plastic cassette Multi-3 - White color with laser printing "COV, FLU, RSV"',
            'min_qty':1000.0,'price':0.05,'currency_id':usd.id,
            'date_start':date(2025,4,23),
        })
        env.cr.commit()
        print(f"  CREADA supplierinfo MPCAR72 <- Cangzhou K067")
    else:
        print(f"  YA OK supplierinfo MPCAR72 <- Cangzhou K067")

# Categoria Semiterminado / Cartucho armado
cat_arm = env['product.category'].search([('complete_name','=','Semiterminado / Cartucho armado')], limit=1)
if not cat_arm:
    parent = env['product.category'].search([('complete_name','=','Semiterminado')], limit=1)
    if not parent: parent = env['product.category'].create({'name':'Semiterminado'})
    cat_arm = env['product.category'].create({'name':'Cartucho armado','parent_id':parent.id})
    env.cr.commit()
    print(f"  CREADA categoria id={cat_arm.id}")

# STCAR_CR01
stcar = env['product.template'].search([('default_code','=','STCAR_CR01')], limit=1)
if not stcar:
    stcar = env['product.template'].create({
        'default_code':'STCAR_CR01',
        'name':'Cartucho Combo Respiratorio armado (Influenza+RSV+COVID)',
        'type':'consu','is_storable':True,'sale_ok':False,'purchase_ok':False,
        'uom_id':unit.id,'categ_id':cat_arm.id,
    })
    env.cr.commit()
    print(f"  CREADO STCAR_CR01 id={stcar.id}")
else:
    print(f"  YA OK STCAR_CR01 id={stcar.id}")

# BoM nivel 1 STCAR_CR01
bom = env['mrp.bom'].search([('code','=','BOM-N1-STCAR_CR01')], limit=1)
if not bom:
    bom = env['mrp.bom'].create({
        'product_tmpl_id':stcar.id,'product_qty':1.0,'type':'normal',
        'code':'BOM-N1-STCAR_CR01','product_uom_id':unit.id,
    })
    comps = [('SPHMC15',0.4,'cm'),('SPHMC20',0.4,'cm'),('SPHMC01',0.4,'cm'),
             ('MPCAR72',1.0,'Units'),('STBTR02',1.0,'Units'),
             ('STHIS01',1.0,'Units'),('MPBOL01',1.0,'Units')]
    cnt=0
    for code,qty,u in comps:
        prod = env['product.product'].search([('default_code','=',code)], limit=1)
        if not prod: 
            print(f"    FALTA componente {code}"); continue
        uom = env['uom.uom'].search([('name','=',u)], limit=1) or prod.uom_id
        env['mrp.bom.line'].create({
            'bom_id':bom.id,'product_id':prod.id,
            'product_qty':qty,'product_uom_id':uom.id,
        })
        cnt+=1
    env.cr.commit()
    print(f"  CREADO BoM N1 STCAR_CR01 con {cnt} lineas")
else:
    print(f"  YA OK BoM N1 id={bom.id}")
