# -*- coding: utf-8 -*-
"""Avisar a Alondra en el chatter de los lotes de ARU que nacieron vencidos.

POR QUE. El corte de inventario de ARU dio de alta 21 reactivos que estaban
fisicamente en el anaquel desde antes de que la casa arrancara con Odoo. Cinco de
ellos ya pasaron su caducidad y uno vence este año. Es correcto que el sistema lo
diga -- es justo lo que no se sabia antes de que existieran --, pero alguien tiene
que decidir que se hace con material vencido en un anaquel de uso, y esa decision
no es del sistema.

Mery pidio el 1-oct-2026 escribirle a Alondra en el chatter de cada lote para que
los revise.

POR QUE EN EL CHATTER DE CADA LOTE Y NO UN SOLO CORREO. El aviso queda pegado al
registro que describe: quien abra ese lote dentro de seis meses encuentra ahi la
pregunta y la respuesta, sin tener que buscar un correo. Para ISO 13485 eso es la
diferencia entre un registro y una conversacion.

Se notifica a Alondra con partner_ids para que le llegue a su bandeja, no solo
quede escrito.

Idempotente: no duplica el mensaje si ya lo puso.
"""
from markupsafe import Markup
from odoo import fields

MARCA = 'Revision de caducidad del corte de ARU'
LOTES = ('REC32102601', 'REC43102601', 'REC41102601',
         'REC91102601', 'REC31102601', 'REC16102601')

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

alondra = env['res.users'].sudo().search(
    [('login', '=', 'produccionsub@amunet.com.mx')], limit=1)
assert alondra, 'No encuentro a Alondra (produccionsub@amunet.com.mx)'
aru = env['stock.location'].sudo().search([('complete_name', '=', 'ARU/Stock')], limit=1)
hoy = fields.Date.context_today(env['stock.lot'])

puestos, ya_tenian = [], []
for nombre in LOTES:
    l = env['stock.lot'].sudo().search([('name', '=', nombre)], limit=1)
    if not l:
        continue
    if any(MARCA in (m.body or '') for m in l.message_ids):
        ya_tenian.append(nombre)
        continue
    cantidad = sum(env['stock.quant'].sudo().search([
        ('lot_id', '=', l.id), ('location_id', '=', aru.id)]).mapped('quantity'))
    cad = l.expiration_date.date() if l.expiration_date else None
    dias = (hoy - cad).days if cad else 0
    estado = ('<b>vencido desde hace %d días</b>' % dias) if dias > 0 else (
        '<b>vence en %d días</b>' % abs(dias))
    l.sudo().message_post(
        body=Markup(
            '<b>%(marca)s</b><br/><br/>'
            'Alondra, este lote acaba de darse de alta en el corte de inventario '
            'de <b>ARU</b> (almacén de reactivos en uso) y está %(estado)s.<br/><br/>'
            '<b>%(clave)s — %(nombre_prod)s</b><br/>'
            'Lote Amunet: <b>%(lote)s</b><br/>'
            'Lote del proveedor: <b>%(prov)s</b><br/>'
            'Caducidad: <b>%(cad)s</b><br/>'
            'Cantidad en ARU: <b>%(cant)s %(uom)s</b><br/><br/>'
            '<b>¿Por qué aparece ahora?</b> Este reactivo estaba físicamente en el '
            'anaquel desde antes de que la casa arrancara con Odoo. Nunca había '
            'entrado al sistema, así que su caducidad tampoco se vigilaba. El corte '
            'del 1-oct-2026 lo registró con la fecha que trae la etiqueta del '
            'frasco, y por eso el semáforo lo marca de inmediato.<br/><br/>'
            '<b>¿Qué necesitamos de ti?</b> Que lo revises físicamente y nos digas '
            'qué procede:<br/>'
            '&bull; <b>Se da de baja</b> — si ya no sirve, se desecha y se registra '
            'la merma.<br/>'
            '&bull; <b>Se revalida</b> — si Calidad puede extender su vida útil con '
            'un análisis, se documenta la extensión.<br/>'
            '&bull; <b>La fecha está mal</b> — si la etiqueta dice otra cosa o la '
            'capturamos mal, se corrige.<br/><br/>'
            'Mientras no se resuelva, el lote queda registrado y marcado: no se '
            'pierde de vista, pero tampoco se usa sin que alguien lo autorice.<br/><br/>'
            '<i>Lo pidió Mery. Cualquier duda del registro, con Desarrollo.</i>'
        ) % {
            'marca': MARCA, 'estado': estado,
            'clave': l.product_id.default_code or '',
            'nombre_prod': l.product_id.name or '',
            'lote': l.name or '',
            'prov': l.factory_lot_id.name or '(no registrado)',
            'cad': cad.strftime('%d/%m/%Y') if cad else '(sin fecha)',
            'cant': ('%g' % cantidad), 'uom': l.product_id.uom_id.name,
        },
        partner_ids=[alondra.partner_id.id],
        subject='Revisar caducidad: %s %s' % (l.product_id.default_code, l.name))
    puestos.append((l.product_id.default_code, l.name, cad, dias, cantidad,
                    l.product_id.uom_id.name))

env.cr.commit()

print('=' * 100)
print('AVISOS PUESTOS EN EL CHATTER, notificando a %s' % alondra.name)
print('=' * 100)
for clave, lote, cad, dias, cant, uom in puestos:
    est = 'vencido hace %d dias' % dias if dias > 0 else 'vence en %d dias' % abs(dias)
    print('   %-9s %-13s %8.2f %-3s caduca %s   %s' % (
        clave, lote, cant, uom, cad.strftime('%d/%m/%Y') if cad else '-', est))
if ya_tenian:
    print('-' * 100)
    print('YA LO TENIAN (no se duplico): %s' % ', '.join(ya_tenian))
print('=' * 100)
