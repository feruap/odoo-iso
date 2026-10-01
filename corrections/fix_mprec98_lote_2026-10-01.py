# -*- coding: utf-8 -*-
"""Arreglar el prefijo de lote de MPREC98 y renombrar el lote que nacio mal.

QUE PASO. Al replicar MPREC98 (EDTA) en staging no le puse el prefijo de lote, y
sin secuencia Amunet `_amunet_next_lot_names` cae al numerador NATIVO de Odoo. El
lote del corte de ARU nacio como **0000001** en vez de **REC98102601**.

En produccion el producto si tiene su secuencia (`REC98%(month)s%(y)s`), asi que
este es un defecto de la replica, no del corte.

SE CORRIGEN LAS DOS COSAS: el prefijo del producto -- para que los proximos lotes
salgan bien -- y el nombre del lote que ya se creo. Renombrar un lote es seguro:
el quant lo referencia por id, no por nombre.

Idempotente.
"""
CLAVE = 'MPREC98'
PREFIJO = 'REC98'

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

p = env['product.product'].sudo().search([('default_code', '=', CLAVE)], limit=1)
assert p, 'No existe %s' % CLAVE
tmpl = p.product_tmpl_id

print('ANTES:  prefijo=%r  secuencia=%s' % (
    tmpl.amunet_lot_prefix,
    tmpl.lot_sequence_id.prefix if tmpl.lot_sequence_id else '(ninguna)'))

# OJO: el producto YA tenia secuencia, pero la NATIVA de Odoo
# (`stock.lot.serial`). `_amunet_next_lot_names` la encontraba y la usaba, y de
# ahi salio el 0000001. La condicion correcta no es "no tiene secuencia" sino
# "no tiene secuencia AMUNET".
if not (tmpl.lot_sequence_id and (tmpl.lot_sequence_id.code or '').startswith('amunet.lot.')):
    # write() + flush, no asignacion por atributo: el campo es store=False con
    # inverse, y asignandolo sin flush el commit se va sin disparar el inverse.
    tmpl.sudo().write({'amunet_lot_prefix': PREFIJO})
    tmpl.flush_recordset()
    env.cr.commit()
    tmpl.invalidate_recordset()
print('DESPUES: prefijo=%r  secuencia=%s' % (
    tmpl.amunet_lot_prefix,
    tmpl.lot_sequence_id.prefix if tmpl.lot_sequence_id else '(ninguna)'))

# renombrar el lote que nacio con el numerador nativo
malos = env['stock.lot'].sudo().search([
    ('product_id', '=', p.id),
    ('name', 'not like', PREFIJO + '%')])
for l in malos:
    nuevos = p.sudo()._amunet_next_lot_names(1)
    if not nuevos or not nuevos[0].startswith(PREFIJO):
        print('   NO pude generar nombre para %s (sale %r)' % (l.name, nuevos))
        continue
    viejo = l.name
    l.sudo().write({'name': nuevos[0]})
    print('   lote renombrado: %s -> %s' % (viejo, nuevos[0]))
env.cr.commit()

print('-' * 70)
for l in env['stock.lot'].sudo().search([('product_id', '=', p.id)]):
    ex = sum(env['stock.quant'].sudo().search([
        ('lot_id', '=', l.id), ('location_id.usage', '=', 'internal')]).mapped('quantity'))
    print('   %-14s %8.2f %s  caduca %s  prov %s' % (
        l.name, ex, p.uom_id.name, str(l.expiration_date)[:10],
        l.factory_lot_id.name or '-'))
