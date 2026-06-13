# Etapa A: Fapon (reusa partner existente si lo hay) + 35 productos + supplierinfo
import json
from datetime import datetime
data = json.load(open('/tmp/fapon_anticuerpos_data.json'))
print(f"Cargando {len(data)} productos Fapon...")

# Buscar partner Fapon existente (cualquier variante de nombre); renombrar a estandar
fapon = env['res.partner'].search([('name','ilike','Fapon')], limit=1)
extra_comment = ('\n--- Datos bancarios Fapon (Hong Kong) ---\n'
                 'Bank: BANK OF CHINA (HONG KONG) LIMITED\n'
                 'Bank account: 01287520109185\n'
                 'SWIFT: BKCHHKHHXXX\n'
                 'Beneficiario: Fapon International Limited (filial HK)\n'
                 'Pago: 50% T/T anticipo, 25% 30d post-envio, 25% 60d post-envio.\n'
                 'EXW Hong Kong.')
if not fapon:
    fapon = env['res.partner'].create({
        'name':'Fapon Biotech Inc.','is_company':True,'company_type':'company',
        'country_id':env.ref('base.hk').id,'city':'Hong Kong',
        'street':'Unit 2205, 22/F, 111-113 How Ming Street',
        'street2':'Futura Plaza, Kwun Tong, Kowloon',
        'ref':'FAPON-HK','comment':extra_comment.strip(),
    })
    print(f"  CREADO Fapon id={fapon.id}")
else:
    vals = {}
    if fapon.name != 'Fapon Biotech Inc.':
        vals['name'] = 'Fapon Biotech Inc.'
    if not fapon.country_id:
        vals['country_id'] = env.ref('base.hk').id
    if 'BKCHHKHHXXX' not in (fapon.comment or ''):
        vals['comment'] = ((fapon.comment or '') + extra_comment).strip()
    if vals: fapon.write(vals)
    print(f"  USANDO Fapon EXISTENTE id={fapon.id} name={fapon.name}")
env.cr.commit()

# Categorias y UoM
mp = env['product.category'].search([('complete_name','=','Materia prima')], limit=1) or env['product.category'].create({'name':'Materia prima'})
def cat(nombre):
    full = f'Materia prima / {nombre}'
    c = env['product.category'].search([('complete_name','=',full)], limit=1)
    if not c:
        c = env['product.category'].create({'name':nombre,'parent_id':mp.id})
        env.cr.commit()
        print(f"  CREADA categoria {full} id={c.id}")
    return c
cat_anti = cat('Anticuerpo')
cat_antg = cat('Antigeno recombinante')
cat_aux  = cat('Reactivo auxiliar')

mg = env['uom.uom'].search([('name','=','mg')], limit=1)
if not mg:
    g = env['uom.uom'].search([('name','=','g')], limit=1)
    mg = env['uom.uom'].create({'name':'mg','factor':1000.0,'relative_factor':0.001,
                                'relative_uom_id':g.id,'rounding':0.001}) if g else env.ref('uom.product_uom_unit')
    env.cr.commit()
    print(f"  CREADA UoM mg id={mg.id}")

usd = env.ref('base.USD')
creados=0; existen=0
for r in data:
    rol = r['rol']
    c_id = (cat_aux if rol=='aux' else cat_antg if rol=='antigen' else cat_anti).id
    p = env['product.template'].search([('default_code','=',r['code'])], limit=1)
    if not p:
        p = env['product.template'].create({
            'default_code':r['code'],'name':r['name'],'type':'consu','is_storable':True,
            'sale_ok':False,'purchase_ok':True,'uom_id':mg.id,'categ_id':c_id,
            'description':f"Catalogo Fapon: {r['catalog_fapon']}\nAnalito: {r['analito']}\nRol: {r['rol']}\nUsado para SPHM: {', '.join(r['sphm'])}",
        })
        creados+=1
    else:
        existen+=1
    dup = env['product.supplierinfo'].search([
        ('product_tmpl_id','=',p.id),('partner_id','=',fapon.id),
        ('product_code','=',r['catalog_fapon'])
    ], limit=1)
    if not dup:
        vals = {'product_tmpl_id':p.id,'partner_id':fapon.id,
                'product_code':r['catalog_fapon'],
                'product_name':r['description_orig'][:128] if r['description_orig'] else r['name'][:128],
                'product_uom_id':mg.id,'min_qty':1.0,'price':r['price_usd_per_mg'],'currency_id':usd.id}
        if r['date_pfi']: vals['date_start']=datetime.strptime(r['date_pfi'],'%Y-%m-%d').date()
        env['product.supplierinfo'].create(vals)
env.cr.commit()
print(f"  Productos: creados={creados} existen={existen}")
