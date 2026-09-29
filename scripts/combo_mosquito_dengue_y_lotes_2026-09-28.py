"""Combo Mosquito: entra la hoja de Dengue que llego y no se registro, mas dos
correcciones de lote.

Autorizado por Mery el 28-sep-2026, con dos decisiones suyas: se acepta el combo
como llego, y si se aprovecha la hoja de Dengue.

EL CASO, para quien lo lea despues:

    Se pidio     I204-4025   COMBO MOSQUITO Zika/Chikungunya    3 hojas
    Llego        I163-4045   COMBO MOSQUITO Dengue/Zika/Chik    4 hojas
    Se registro  I204-4025   -- el que se pidio, no el que llego

Y resulta que lo que llego es lo que se necesita: la receta del Combo Mosquito
terminado (DMDCZ01) consume las CUATRO hojas, 0.40 cm de cada una. Con el combo de
tres hojas no se puede fabricar. El error estuvo en el PEDIDO, no en la entrega.

La conversion CONV/00010 genero 900 cm de SPHMC86, 87 y 88, pero no los 900 cm de
SPHMC85 (Dengue), que si llegaron fisicamente.

QUE HACE:

1. Da de alta 900 cm de SPHMC85 en cuarentena, con su lote de septiembre, junto a
   sus tres hermanas. 30 combos x 30 cm = 900 cm, la misma cuenta que las otras.

2. NO ajusta el inventario de los combos, y no es un olvido: los dos estan en CERO
   y eso es lo correcto -- del I204 no llego ninguno, y los 30 del I163 se
   convirtieron en hojas. Un ajuste moveria cantidades que ya estan bien. Lo que
   corresponde ahi es la anotacion, y se deja en la recepcion, en la conversion y
   en los dos productos.

3. Corrige el lote HMC62072602 de SPHMC86: lleva el prefijo de SPHMC62. Es residuo
   de las correcciones de clave que Karla autorizo limpiar; su gemelo ya se
   renombro y este se quedo.

4. Corrige el negativo de SPHMC62: la orden 0926/01/ZKC consumio 1.20 cm el 25-sep
   desde existencias sin haberlas, y dejo -1.20. El material se uso de verdad, solo
   no estaba registrado.

Idempotente.
"""
from markupsafe import Markup

PT = env['product.template'].sudo()
Prod = env['product.product'].sudo()
Lot = env['stock.lot'].sudo()
Quant = env['stock.quant'].sudo()
Loc = env['stock.location'].sudo()

cuarentena = Loc.search([('complete_name', '=', 'AMP/Entrada/Control de calidad')], limit=1)
existencias = Loc.search([('complete_name', '=', 'AMP/Existencias')], limit=1)
assert cuarentena and existencias, 'no encontre las ubicaciones'

def dar_de_alta(clave, nombre_lote, cantidad, ubicacion, motivo):
    prod = Prod.search([('default_code', '=', clave)], limit=1)
    if not prod:
        print('[ojo] %s no existe' % clave); return
    lote = Lot.search([('name', '=', nombre_lote), ('product_id', '=', prod.id)], limit=1)
    if not lote:
        lote = Lot.create({'name': nombre_lote, 'product_id': prod.id,
                           'company_id': env.company.id})
        print('   lote creado: %s' % nombre_lote)
    q = Quant.search([('product_id', '=', prod.id), ('lot_id', '=', lote.id),
                      ('location_id', '=', ubicacion.id)], limit=1)
    actual = q.quantity if q else 0.0
    if abs(actual - cantidad) < 0.0001:
        print('[ya] %s lote %s ya tiene %g en %s' % (
            clave, nombre_lote, cantidad, ubicacion.complete_name)); return
    if not q:
        q = Quant.with_context(inventory_mode=True).create({
            'product_id': prod.id, 'lot_id': lote.id,
            'location_id': ubicacion.id, 'inventory_quantity': cantidad})
    else:
        q.with_context(inventory_mode=True).write({'inventory_quantity': cantidad})
    q.with_context(inventory_mode=True).action_apply_inventory()
    print('[ok] %s lote %s: %g -> %g en %s' % (
        clave, nombre_lote, actual, cantidad, ubicacion.complete_name))
    lote.message_post(body=Markup(motivo))

# ---------------------------------------------------- 1. la hoja de Dengue
print('-- 1. SPHMC85 (Dengue), los 900 cm que llegaron en el combo --')
dar_de_alta('SPHMC85', 'HMC85092601', 900.0, cuarentena, (
    'Alta de <b>900 cm</b> en cuarentena, autorizada por Mery el 28-sep-2026.'
    '<br/><br/>Llegaron en la recepcion AMP/IN/00347 (orden P00214, Hangzhou '
    'Tongzhou): se pidio el combo I204-4025 de TRES hojas y el proveedor mando el '
    'I163-4045 de CUATRO, que incluye esta hoja de Dengue. Se registro el que se '
    'pidio, asi que la conversion CONV/00010 genero las otras tres hojas y esta se '
    'quedo sin dar de alta.<br/><br/>30 combos x 30 cm = 900 cm, la misma cuenta '
    'que sus tres hermanas (SPHMC86, 87 y 88, lotes HMC8x092601).<br/><br/>'
    'Mery acepto el material como llego y autorizo aprovecharlo. <b>Falta que '
    'Calidad genere su analisis</b>: sin el no sale de cuarentena.'))

# ---------------------------------------------------- 2. la anotacion del combo
print('\n-- 2. anotacion de que combo llego de verdad --')
NOTA = Markup(
    'Aclaracion de trazabilidad, 28-sep-2026, autorizada por Mery: el combo que '
    'llego fisicamente fue <b>I163-4045</b> (Dengue/Zika/Chikungunya, cuatro hojas) '
    'y no el I204-4025 (tres hojas) que se pidio en P00214 y que quedo registrado '
    'aqui.<br/><br/>La receta del Combo Mosquito terminado (DMDCZ01) consume las '
    'CUATRO hojas, asi que lo recibido es lo que se necesita: el error estuvo en el '
    'pedido, no en la entrega. Mery acepto el material como llego.<br/><br/>'
    'El inventario de los dos combos NO se ajusto porque ya esta correcto: los dos '
    'en cero -- del I204 no llego ninguno y los 30 del I163 se convirtieron en '
    'hojas. Lo que faltaba era la hoja de Dengue, que se dio de alta como '
    'HMC85092601 (900 cm).')
for modelo, nombre in (('stock.picking', 'AMP/IN/00347'),
                       ('stock.picking', 'CONV/00010')):
    rec = env[modelo].sudo().search([('name', '=', nombre)], limit=1)
    if not rec:
        print('   [ojo] no existe %s' % nombre); continue
    ya = env['mail.message'].sudo().search_count([
        ('model', '=', modelo), ('res_id', '=', rec.id),
        ('body', 'like', 'Aclaracion de trazabilidad')])
    if ya:
        print('   [ya] %s ya tiene la aclaracion' % nombre); continue
    rec.message_post(body=NOTA)
    print('   [ok] aclaracion anotada en %s' % nombre)
for clave in ('I163-4045', 'I204-4025'):
    t = PT.search([('default_code', '=', clave)], limit=1)
    if not t: continue
    ya = env['mail.message'].sudo().search_count([
        ('model', '=', 'product.template'), ('res_id', '=', t.id),
        ('body', 'like', 'Aclaracion de trazabilidad')])
    if ya:
        print('   [ya] %s ya tiene la aclaracion' % clave); continue
    t.message_post(body=NOTA)
    print('   [ok] aclaracion anotada en el producto %s' % clave)

# ---------------------------------------------------- 3. el lote de SPHMC86
print('\n-- 3. lote de SPHMC86 con prefijo de otra hoja --')
p86 = Prod.search([('default_code', '=', 'SPHMC86')], limit=1)
malo = Lot.search([('name', '=', 'HMC62072602'), ('product_id', '=', p86.id)], limit=1)
ocupado = Lot.search([('name', '=', 'HMC86072602'), ('product_id', '=', p86.id)], limit=1)
if not malo:
    print('[ya] %s' % ('ya se llama HMC86072602' if ocupado else 'no existe el lote HMC62072602 de SPHMC86'))
elif ocupado:
    print('NO SE RENOMBRA: HMC86072602 ya lo tiene el lote %s' % ocupado.id)
else:
    liberado = env['amunet.quality.check'].sudo().search([('lot_id', '=', malo.id)]).filtered(
        lambda c: c.state == 'done' or c.user_authorized_id)
    if liberado:
        print('NO SE TOCA: su analisis %s esta liberado' % ', '.join(liberado.mapped('name')))
    else:
        malo.write({'name': 'HMC86072602'})
        malo.message_post(body=Markup(
            'Lote renombrado de <b>HMC62072602</b> a <b>HMC86072602</b> el 28-sep-2026, '
            'autorizado por Mery y confirmado por Karla.<br/><br/>Llevaba el prefijo de '
            'SPHMC62 siendo un lote de SPHMC86: residuo de las correcciones de clave. Su '
            'gemelo (HMC62072601) ya se habia renombrado y este se quedo. Sin analisis.'))
        print('[ok] HMC62072602 -> HMC86072602  (SPHMC86)')

# ---------------------------------------------------- 4. el negativo de SPHMC62
print('\n-- 4. el negativo de SPHMC62 --')
p62 = Prod.search([('default_code', '=', 'SPHMC62')], limit=1)
lote62 = Lot.search([('name', '=', 'HMC62092601'), ('product_id', '=', p62.id)], limit=1)
if not lote62:
    print('[ojo] no existe el lote HMC62092601')
else:
    q = Quant.search([('product_id', '=', p62.id), ('lot_id', '=', lote62.id),
                      ('location_id', '=', existencias.id)], limit=1)
    actual = q.quantity if q else 0.0
    if actual >= 0:
        print('[ya] el lote %s esta en %g, sin negativo' % (lote62.name, actual))
    else:
        q.with_context(inventory_mode=True).write({'inventory_quantity': 0.0})
        q.with_context(inventory_mode=True).action_apply_inventory()
        print('[ok] SPHMC62 lote %s: %g -> 0 en %s' % (
            lote62.name, actual, existencias.complete_name))
        lote62.message_post(body=Markup(
            'Se corrige una existencia NEGATIVA de %g cm, autorizado por Mery el '
            '28-sep-2026.<br/><br/>La orden de produccion <b>0926/01/ZKC</b> consumio '
            '1.20 cm de esta hoja el 25-sep desde AMP/Existencias sin que hubiera '
            'existencia registrada, y dejo el lote en negativo. El material se uso de '
            'verdad; lo que faltaba era su alta. Se sube a cero para que el almacen '
            'refleje la realidad.' % actual))

print('\n=== como queda ===')
for clave in ('SPHMC85', 'SPHMC86', 'SPHMC87', 'SPHMC88'):
    p = Prod.search([('default_code', '=', clave)], limit=1)
    for x in Quant.search([('product_id', '=', p.id), ('location_id.usage', '=', 'internal')]):
        if not x.quantity:
            continue
        print('   %-9s %-13s %10g  %s' % (clave, x.lot_id.name or '-', x.quantity,
                                          x.location_id.complete_name))
p = Prod.search([('default_code', '=', 'SPHMC62')], limit=1)
neg = Quant.search([('product_id', '=', p.id), ('location_id.usage', '=', 'internal')]).filtered(
    lambda q: q.quantity < 0)
print('   SPHMC62 con negativo: %s' % (neg.mapped('lot_id.name') or 'ninguno'))
env.cr.commit()
