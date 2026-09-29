"""EQGOG01: entran las 30 piezas que hay, y se asienta lo que falta saber.

Indicaciones de Mery, 28-sep-2026:
  - el precio de venta lo pone Fernando
  - la caja trae UNA pieza
  - NO hay modelo / numero de parte
  - cargar el inventario real: 30 piezas
  - avisarle a Fernando del alta para que el lo publique o lo venda donde quiera

DONDE ENTRAN: ADT/Stock, el almacen de Distribucion, que es donde vive este
producto (se compra para vender). Con su lote, porque lleva trazabilidad por lote:
el nombre sale de su prefijo, configurado hoy (GOG01 + mes + anio).

LO DE "1 PIEZA POR CAJA" no va en amunet_contenido_envase: ese campo es para
material que se guarda por envase y se consume por volumen (el agua en garrafones).
Aqui la unidad ya es Unidades y cada unidad ES su caja, asi que no hace falta
ningun campo: queda asentado en el historial del producto para quien lo consulte.

Idempotente: si ya hay 30 piezas, no vuelve a cargar.
"""

PT = env['product.template'].sudo()
Lot = env['stock.lot'].sudo()
Quant = env['stock.quant'].sudo()

CLAVE, PIEZAS = 'EQGOG01', 30.0
tmpl = PT.search([('default_code', '=', CLAVE)], limit=1)
assert tmpl, 'no existe %s' % CLAVE
prod = tmpl.product_variant_id
alm = env['stock.warehouse'].sudo().search([('code', '=', 'ADT')], limit=1)
assert alm, 'no existe el almacen ADT'
ubic = alm.lot_stock_id

# --- la nota de lo que se sabe del producto
NOTA = ('Datos confirmados por Mery el 28-sep-2026: la caja trae <b>1 pieza</b> y '
        'el producto <b>no tiene modelo ni numero de parte</b> (la etiqueta del '
        'costado no lo indica). El <b>precio de venta lo define Fernando</b>; '
        'queda en 0 a proposito hasta que el lo capture.')
from markupsafe import Markup
ya_anotado = env['mail.message'].sudo().search_count([
    ('model', '=', 'product.template'), ('res_id', '=', tmpl.id),
    ('body', 'like', 'la caja trae')])
if ya_anotado:
    print('[ya] la nota de la caja y el modelo ya esta en el historial')
else:
    tmpl.message_post(body=Markup(NOTA))
    print('[ok] anotado en el historial: 1 pieza por caja, sin modelo, precio de Fernando')

# --- el lote
lote = Lot.search([('product_id', '=', prod.id)], limit=1)
if not lote:
    nombre = prod.product_tmpl_id.next_serial or ''
    if not nombre:
        seq = tmpl.lot_sequence_id
        nombre = seq.next_by_id() if seq else 'GOG01092601'
    lote = Lot.create({'name': nombre, 'product_id': prod.id,
                       'company_id': env.company.id})
    print('[ok] lote creado: %s' % lote.name)
else:
    print('[ya] usa el lote existente: %s' % lote.name)

# --- el inventario
q = Quant.search([('product_id', '=', prod.id), ('location_id', '=', ubic.id),
                  ('lot_id', '=', lote.id)], limit=1)
actual = q.quantity if q else 0.0
if abs(actual - PIEZAS) < 0.0001:
    print('[ya] ya hay %g piezas en %s' % (PIEZAS, ubic.complete_name))
else:
    if not q:
        q = Quant.with_context(inventory_mode=True).create({
            'product_id': prod.id, 'location_id': ubic.id, 'lot_id': lote.id,
            'inventory_quantity': PIEZAS})
    else:
        q.with_context(inventory_mode=True).write({'inventory_quantity': PIEZAS})
    q.with_context(inventory_mode=True).action_apply_inventory()
    print('[ok] inventario: %g -> %g piezas en %s (lote %s)' % (
        actual, PIEZAS, ubic.complete_name, lote.name))
    lote.message_post(body=Markup(
        'Alta de inventario inicial: <b>%g piezas</b> en %s, confirmadas por Mery '
        'el 28-sep-2026. Material recibido por Luis; el producto se dio de alta el '
        'mismo dia con la clave que asigno Documentacion.' % (PIEZAS, ubic.complete_name)))

print('\n=== como queda ===')
tmpl.invalidate_recordset()
print('   %s  %s' % (CLAVE, tmpl.name))
print('   categoria: %s   vive en: %s   unidad: %s' % (
    tmpl.categ_id.complete_name, tmpl.amunet_destino_almacen, tmpl.uom_id.name))
print('   precio de venta: %g   (lo define Fernando)' % tmpl.list_price)
for x in Quant.search([('product_id', '=', prod.id),
                       ('location_id.usage', '=', 'internal')]):
    print('   existencia: %g en %s   lote %s' % (
        x.quantity, x.location_id.complete_name, x.lot_id.name or '-'))
env.cr.commit()
