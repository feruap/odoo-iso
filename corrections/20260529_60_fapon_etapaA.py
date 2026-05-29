# Etapa A: Fapon International Limited + categoria + 35 productos (anticuerpos/antigenos/aux) + supplierinfo
# Idempotente.
import json
from datetime import datetime
data = json.load(open('/tmp/fapon_anticuerpos_data.json'))
print(f"Cargando {len(data)} productos Fapon...")

# 1) Proveedor Fapon
fapon = env['res.partner'].search([('name','ilike','Fapon International')], limit=1)
if not fapon:
    fapon = env['res.partner'].create({
        'name': 'Fapon International Limited',
        'is_company': True,
        'company_type': 'company',
        'country_id': env.ref('base.hk').id,
        'city': 'Hong Kong',
        'street': 'Unit 2205, 22/F, 111-113 How Ming Street',
        'street2': 'Futura Plaza, Kwun Tong, Kowloon',
        'ref': 'FAPON-HK',
        'comment': ('Proveedor de materias primas para IVD: anticuerpos monoclonales, antigenos recombinantes y reactivos auxiliares.\n'
                    'Bank: BANK OF CHINA (HONG KONG) LIMITED\n'
                    'Bank account: 01287520109185\n'
                    'SWIFT: BKCHHKHHXXX\n'
                    'Bank address: BANK OF CHINA TOWER, 1 GARDEN ROAD, CENTRAL, HONG KONG\n'
                    'Pago: 50% T/T anticipo, 25% 30 dias post-envio, 25% 60 dias post-envio.\n'
                    'EXW Hong Kong.'),
    })
    env.cr.commit()
    print(f"  CREADO Fapon id={fapon.id}")
else:
    print(f"  YA OK Fapon id={fapon.id}")

# 2) Categorias Anticuerpo, Antigeno y Reactivo auxiliar (bajo Materia prima)
mp = env['product.category'].search([('complete_name','=','Materia prima')], limit=1)
if not mp:
    mp = env['product.category'].create({'name':'Materia prima'})

def cat(nombre):
    full = f'Materia prima / {nombre}'
    c = env['product.category'].search([('complete_name','=',full)], limit=1)
    if not c:
        c = env['product.category'].create({'name': nombre, 'parent_id': mp.id})
        env.cr.commit()
        print(f"  CREADA categoria {full} id={c.id}")
    return c

cat_anti = cat('Anticuerpo')
cat_antg = cat('Antigeno recombinante')
cat_aux  = cat('Reactivo auxiliar')

# 3) UoM mg
mg = env['uom.uom'].search([('name','=','mg')], limit=1)
if not mg:
    # Buscar categoria peso o crear UoM
    g = env['uom.uom'].search([('name','=','g')], limit=1)
    if g:
        mg = env['uom.uom'].create({
            'name':'mg', 'factor':1000.0, 'relative_factor':0.001,
            'relative_uom_id':g.id, 'rounding':0.001,
        })
        env.cr.commit()
        print(f"  CREADA UoM mg id={mg.id}")
    else:
        mg = env.ref('uom.product_uom_unit')  # fallback
        print("  AVISO: UoM g no existe, uso Units como fallback para mg")

usd = env.ref('base.USD')

# 4) Productos
creados=0; existen=0
for r in data:
    rol = r['rol']
    if rol == 'aux': c_id = cat_aux.id
    elif rol == 'antigen': c_id = cat_antg.id
    elif rol == 'secondary': c_id = cat_anti.id  # secundarios bajo Anticuerpo
    else: c_id = cat_anti.id
    p = env['product.template'].search([('default_code','=',r['code'])], limit=1)
    if not p:
        p = env['product.template'].create({
            'default_code': r['code'],
            'name': r['name'],
            'type': 'consu',
            'is_storable': True,
            'sale_ok': False,
            'purchase_ok': True,
            'uom_id': mg.id,
            'categ_id': c_id,
            'description': f"Catalogo Fapon: {r['catalog_fapon']}\nAnalito: {r['analito']}\nRol: {r['rol']}\nUsado para SPHM: {', '.join(r['sphm'])}",
        })
        creados+=1
    else:
        existen+=1
    # supplierinfo
    dup = env['product.supplierinfo'].search([
        ('product_tmpl_id','=',p.id),('partner_id','=',fapon.id),
        ('product_code','=',r['catalog_fapon']),
    ], limit=1)
    if not dup:
        vals = {
            'product_tmpl_id': p.id, 'partner_id': fapon.id,
            'product_code': r['catalog_fapon'],
            'product_name': r['description_orig'][:128] if r['description_orig'] else r['name'][:128],
            'product_uom_id': mg.id,
            'min_qty': 1.0,
            'price': r['price_usd_per_mg'],
            'currency_id': usd.id,
        }
        if r['date_pfi']:
            vals['date_start'] = datetime.strptime(r['date_pfi'],'%Y-%m-%d').date()
        env['product.supplierinfo'].create(vals)
env.cr.commit()
print(f"\n  Productos: creados={creados} ya_existen={existen}")
print(f"  supplierinfo Fapon: cargados.")
