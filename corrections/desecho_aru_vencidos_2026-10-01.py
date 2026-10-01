# -*- coding: utf-8 -*-
"""Desechar los 5 reactivos vencidos de ARU. El BSA se queda.

DECISION. Alondra reviso los 6 lotes que el corte de ARU dio de alta vencidos o
por vencer, y respondio por Discuss: **la albumina se queda, lo demas se elimina**.
Mery lo transmitio el 1-oct-2026.

El BSA (MPREC16, REC16102601, 25 g) **no se toca**: vence el 01-11-2026, le quedan
31 dias, y Alondra decidio conservarlo. Sigue en ARU con su caducidad y el semaforo
lo seguira marcando conforme se acerque, que es lo correcto.

POR QUE stock.scrap Y NO UN AJUSTE A CERO. Un ajuste de inventario dejaria la
existencia en cero sin decir QUE PASO con el material: parece que nunca estuvo. El
desecho deja el registro con producto, lote, cantidad, de donde salio y a donde
fue. Para Cofepris esa diferencia importa -- el desperdicio se asienta, no se
evapora. Es el mismo criterio que ya usa la casa para el sobrante de conjugados
(amunet_production: _amunet_desechar_sobrante).

QUEDA ASENTADO QUIEN DECIDIO. En el `origin` de cada desecho y en el chatter del
lote: Alondra reviso, Mery autorizo, con fecha. Un desecho sin responsable es un
hueco en la trazabilidad.

Idempotente: no desecha dos veces el mismo lote.
"""
from markupsafe import Markup
from odoo import _

SE_QUEDA = {'REC16102601': 'albumina de suero bovino (BSA) — decision de Alondra'}
A_DESECHAR = ('REC32102601', 'REC43102601', 'REC41102601', 'REC91102601', 'REC31102601')
MOTIVO = 'Vencido — corte de inventario ARU 01-oct-2026, revisado por Alondra'

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

aru = env['stock.location'].sudo().search(
    [('complete_name', '=', 'ARU/Stock'), ('usage', '=', 'internal')], limit=1)
scrap_loc = env.ref('stock.stock_location_scrapped', raise_if_not_found=False)
assert aru and scrap_loc, 'Falta ARU/Stock o la ubicacion de desecho'

desechados, ya_estaban, problemas = [], [], []
for nombre in A_DESECHAR:
    l = env['stock.lot'].sudo().search([('name', '=', nombre)], limit=1)
    if not l:
        problemas.append((nombre, 'el lote no existe')); continue
    p = l.product_id
    q = env['stock.quant'].sudo().search([
        ('lot_id', '=', l.id), ('location_id', '=', aru.id)], limit=1)
    cantidad = q.quantity if q else 0.0
    if cantidad <= 0:
        ya_estaban.append((p.default_code, nombre, 'ya estaba en cero en ARU')); continue
    yadesecho = env['stock.scrap'].sudo().search_count([
        ('lot_id', '=', l.id), ('state', '=', 'done'),
        ('origin', 'like', 'corte de inventario ARU')])
    if yadesecho:
        ya_estaban.append((p.default_code, nombre, 'ya tenia desecho registrado')); continue

    scrap = env['stock.scrap'].sudo().create({
        'product_id': p.id,
        'product_uom_id': p.uom_id.id,
        'lot_id': l.id,
        'scrap_qty': cantidad,
        'location_id': aru.id,
        'scrap_location_id': scrap_loc.id,
        'origin': MOTIVO,
        'company_id': env.company.id,
    })
    scrap.action_validate()
    cad = str(l.expiration_date)[:10] if l.expiration_date else '(sin fecha)'
    l.sudo().message_post(body=Markup(
        '<b>Lote desechado por caducidad</b><br/><br/>'
        'Se mandaron a desecho <b>%(cant)g %(uom)s</b> desde <b>ARU/Stock</b> con el '
        'documento <b>%(doc)s</b>.<br/><br/>'
        'Caducó el <b>%(cad)s</b>. El lote se dio de alta en el corte de inventario '
        'de ARU del 1-oct-2026: estaba físicamente en el anaquel desde antes de que '
        'la casa arrancara con Odoo, así que su caducidad no se vigilaba.<br/><br/>'
        '<b>Quién decidió:</b> lo revisó <b>Alondra Sánchez</b> (Producción) con el '
        'frasco en la mano y determinó que ya no sirve. Autorizado por <b>Mery '
        'Olivares</b> (Desarrollo) el 1-oct-2026.<br/><br/>'
        '<i>Se registra como desecho y no como ajuste a cero a propósito: el ajuste '
        'dejaría la existencia en cero sin decir qué pasó con el material.</i>'
    ) % {'cant': cantidad, 'uom': p.uom_id.name, 'doc': scrap.name, 'cad': cad})
    desechados.append((p.default_code, p.name, nombre, cantidad, p.uom_id.name, cad, scrap.name))

env.cr.commit()

print('=' * 106)
print('DESECHO DE LOTES VENCIDOS DE ARU')
print('=' * 106)
print('DESECHADOS: %d' % len(desechados))
for clave, nombre, lote, cant, uom, cad, doc in desechados:
    print('   %-9s %-28s %-13s %8.2f %-3s caducó %s   doc %s' % (
        clave, nombre[:28], lote, cant, uom, cad, doc))
if ya_estaban:
    print('-' * 106)
    for clave, lote, m in ya_estaban:
        print('   SIN CAMBIO %-9s %-13s %s' % (clave, lote, m))
if problemas:
    print('-' * 106)
    for lote, m in problemas:
        print('   PROBLEMA %-13s %s' % (lote, m))
print('-' * 106)
print('SE QUEDA, por decision de Alondra:')
for nombre, por in SE_QUEDA.items():
    l = env['stock.lot'].sudo().search([('name', '=', nombre)], limit=1)
    if l:
        c = sum(env['stock.quant'].sudo().search([
            ('lot_id', '=', l.id), ('location_id', '=', aru.id)]).mapped('quantity'))
        print('   %-9s %-13s %8.2f %-3s caduca %s   %s' % (
            l.product_id.default_code, l.name, c, l.product_id.uom_id.name,
            str(l.expiration_date)[:10], por))
print('-' * 106)
env.cr.execute("""
    SELECT count(*), round(sum(q.quantity)::numeric,2)
    FROM stock_quant q JOIN stock_location sl ON sl.id=q.location_id
    WHERE sl.complete_name='ARU/Stock' AND q.quantity<>0
""")
n, t = env.cr.fetchone()
print('ARU/Stock queda con %s renglones' % n)
print('=' * 106)
