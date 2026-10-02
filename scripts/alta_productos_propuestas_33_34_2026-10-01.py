# Alta del producto de la propuesta 34 (Cinta testigo para esterilizar,
# COCIT01). Se hace por consola porque el boton "Crear producto" esta roto en
# produccion: crea con sudo() sin el contexto amunet_alta_autorizada y el
# candado lo rechaza. El arreglo ya esta en staging (687566f7) pero su deploy
# esta bloqueado por trabajo sin commitear de otra sesion en
# /opt/odoo/production. Mery no puede esperar: tiene mas propuestas que aprobar.
#
# Esto replica EXACTAMENTE lo que hara el boton arreglado: alta autorizada,
# con su clave, ligada a la propuesta, que pasa a "convertida".
from odoo.api import Environment
mery = Environment(env.cr, 61, {})     # el alta queda a su nombre, no del bot
prop = mery['amunet.marketplace.product.proposal'].browse(34)
print('propuesta:', prop.name, '| clave:', prop.clave_propuesta,
      '| estado:', prop.state, '| categoria:', prop.category_id.complete_name)

clave = (prop.clave_propuesta or '').strip()
ya = env['product.template'].sudo().with_context(active_test=False).search(
    [('default_code', '=', clave)], limit=1)
if ya:
    print('YA EXISTE un producto con esa clave:', ya.name, '-> no se crea otro')
else:
    producto = mery['product.template'].sudo().with_context(
        amunet_alta_autorizada=True).create({
            'name': prop.name,
            'default_code': clave,
            'categ_id': prop.category_id.id,
            'marketplace_enabled': True,
            'marketplace_flow': prop.request_type,
            'marketplace_purchase_url': prop.purchase_url,
            'image_1920': prop.image_1920,
            'purchase_ok': True,
            'sale_ok': False,
            'is_storable': True,
        })
    prop.with_context(marketplace_proposal_internal_write=True).write({
        'product_tmpl_id': producto.id, 'state': 'converted'})
    prop.message_post(body=(
        'Producto dado de alta: <b>%s</b>. Se hizo desde consola con alta '
        'autorizada porque el boton "Crear producto" estaba rechazando el alta '
        '(creaba con superusuario sin marcar que era un alta autorizada). Ya '
        'quedo corregido; el arreglo entra a produccion en el proximo deploy.'
    ) % producto.display_name)
    env.cr.commit()
    print()
    print('CREADO:', producto.default_code, '-', producto.name)
    print('  categoria :', producto.categ_id.complete_name)
    print('  catalogo  :', producto.marketplace_enabled, '| flujo:', producto.marketplace_flow)
    print('  liga      :', (producto.marketplace_purchase_url or '')[:70])
    print('  propuesta :', prop.state)

print()
print('=== otras propuestas esperando ===')
for p in env['amunet.marketplace.product.proposal'].search(
        [('state', 'not in', ('converted', 'rejected'))], order='state,id'):
    print('   %-3s %-11s %-34s clave: %-10s %s' % (
        p.id, p.state, (p.name or '')[:34],
        p.clave_propuesta or '(SIN CLAVE)',
        p.category_id.complete_name or '(sin categoria)'))
