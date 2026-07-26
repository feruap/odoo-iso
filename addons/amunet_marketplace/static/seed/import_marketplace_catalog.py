import base64
import csv
from pathlib import Path


SEED_DIR = Path('/opt/amunet-addons/amunet_marketplace/static/seed')
CSV_PATH = SEED_DIR / 'productos_marketplace_catalogo.csv'

production_terms = (
    'agar', 'peptonada', 'pcr', 'pipeta', 'petri', 'mechero', 'autoclave',
    'erlenmeyer', 'fraser', 'triptona', 'mueller', 'bromofenol', 'elisa',
    'centrífuga', 'centrifuga', 'probeta', 'jeringa', 'microplaca',
    'termohigrómetro', 'termohigrometro', 'varilla agitadora', 'micro sd',
    'báscula', 'bascula', 'rack de puntas',
)


def infer_flow(name):
    lowered = (name or '').lower()
    for term in production_terms:
        if term in lowered:
            return 'production'
    return 'general'


def get_category(env, flow):
    root = env['product.category'].search([('name', '=', 'Marketplace Interno')], limit=1)
    if not root:
        root = env['product.category'].create({'name': 'Marketplace Interno'})
    child_name = 'Produccion' if flow == 'production' else 'Compra general'
    child = env['product.category'].search([
        ('name', '=', child_name),
        ('parent_id', '=', root.id),
    ], limit=1)
    if not child:
        child = env['product.category'].create({
            'name': child_name,
            'parent_id': root.id,
        })
    return child


ProductTemplate = env['product.template'].sudo()

with CSV_PATH.open('r', encoding='utf-8-sig', newline='') as handle:
    rows = list(csv.DictReader(handle))

for row in rows:
    name = (row.get('producto_normalizado') or '').strip()
    if not name:
        continue
    flow = infer_flow(name)
    category = get_category(env, flow)
    image_local = (row.get('imagen_local') or '').strip()
    image_b64 = False
    if image_local:
        local_path = Path(image_local)
        if local_path.exists():
            image_b64 = base64.b64encode(local_path.read_bytes())
        else:
            seed_image = SEED_DIR / 'imagenes' / local_path.name
            if seed_image.exists():
                image_b64 = base64.b64encode(seed_image.read_bytes())

    vals = {
        'name': name,
        'categ_id': category.id,
        'purchase_ok': True,
        'sale_ok': False,
        'is_storable': True,
        'marketplace_enabled': True,
        'marketplace_flow': flow,
        'marketplace_purchase_url': row.get('url_producto') or False,
    }
    if image_b64:
        vals['image_1920'] = image_b64

    product = ProductTemplate.search([
        '|',
        ('marketplace_purchase_url', '=', row.get('url_producto') or ''),
        ('name', '=', name),
    ], limit=1)
    if product:
        product.write(vals)
        print(f'UPDATED\t{name}')
    else:
        ProductTemplate.create(vals)
        print(f'CREATED\t{name}')

env.cr.commit()
print(f'COMMIT_OK\t{len(rows)}')
