# -*- coding: utf-8 -*-
"""Mandarle a Alondra los lotes vencidos de ARU por una conversacion de Odoo.

POR QUE NO BASTO EL CHATTER. El aviso se puso en el chatter de cada lote
mencionando a Alondra (aviso_alondra_lotes_vencidos_2026-10-01.py), pero **no le
llego**. Al revisarlo: Odoo creo la notificacion con
`notification_type='email'` y `notification_status='exception'` -- intento
mandarsela por correo, el envio fallo, y la marco como leida. A su bandeja de Odoo
nunca entro nada.

LA CAUSA: no es seguidora del lote, y a un mencionado que no sigue el registro Odoo
le manda correo en vez de notificacion interna, sobre todo con subtipo "Note".

Asi que el mensaje va por **Discuss**, que es donde si lo va a ver. El chatter de
cada lote se queda como esta -- ahi el registro sirve para la auditoria, pegado al
lote que describe --, y la conversacion es para que ella se entere.

Instruccion de Mery, 1-oct-2026: "no le aparece el mensaje a Alondra mandalo en
una conversacion por odoo".

UN SOLO MENSAJE CON LOS SEIS, no seis mensajes: en un chat, seis mensajes seguidos
del mismo tema se leen como ruido y se responde solo al ultimo.

Idempotente: no lo repite si ya lo mando.
"""
from markupsafe import Markup
from odoo import fields

MARCA = 'Revisar caducidad de 6 reactivos de ARU'

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

alondra = env['res.users'].sudo().search(
    [('login', '=', 'produccionsub@amunet.com.mx')], limit=1)
assert alondra, 'No encuentro a Alondra'
aru = env['stock.location'].sudo().search([('complete_name', '=', 'ARU/Stock')], limit=1)
hoy = fields.Date.context_today(env['stock.lot'])

LOTES = ('REC32102601', 'REC43102601', 'REC41102601',
         'REC91102601', 'REC31102601', 'REC16102601')

renglones, datos = [], []
for nombre in LOTES:
    l = env['stock.lot'].sudo().search([('name', '=', nombre)], limit=1)
    if not l:
        continue
    cant = sum(env['stock.quant'].sudo().search([
        ('lot_id', '=', l.id), ('location_id', '=', aru.id)]).mapped('quantity'))
    cad = l.expiration_date.date() if l.expiration_date else None
    dias = (hoy - cad).days if cad else 0
    datos.append((l, cant, cad, dias))

datos.sort(key=lambda x: -x[3])
for l, cant, cad, dias in datos:
    estado = ('vencido hace <b>%d días</b>' % dias) if dias > 0 else (
        'vence en <b>%d días</b>' % abs(dias))
    renglones.append(
        '<li><b>%s</b> &mdash; %s<br/>'
        'lote <b>%s</b> &middot; %g %s en ARU &middot; caducó %s &middot; %s<br/>'
        '<i>lote del proveedor: %s</i></li>' % (
            l.product_id.default_code or '', l.product_id.name or '',
            l.name, cant, l.product_id.uom_id.name,
            cad.strftime('%d/%m/%Y') if cad else '(sin fecha)', estado,
            l.factory_lot_id.name or 'no registrado'))

canal = env['discuss.channel'].sudo()._get_or_create_chat(
    partners_to=[alondra.partner_id.id, mery.partner_id.id])

ya = any(MARCA in (m.body or '') for m in canal.message_ids)
if ya:
    print('Ya se le habia mandado por Discuss. No se repite.')
else:
    canal.sudo().with_user(mery).message_post(
        body=Markup(
            'Hola Alondra. <b>%(marca)s</b><br/><br/>'
            'Acabamos de hacel el corte de inventario del almacén <b>ARU</b> '
            '(reactivos en uso) y dimos de alta 21 reactivos que estaban en el '
            'anaquel desde antes de que la casa arrancara con Odoo. Nunca habían '
            'entrado al sistema, así que su caducidad tampoco se vigilaba.<br/><br/>'
            '<b>Seis ya pasaron su fecha o están por pasarla</b>, y necesitamos que '
            'los revises físicamente:<br/><ul>%(lista)s</ul>'
            '<b>¿Qué necesitamos de ti?</b> Que los veas con el frasco en la mano y '
            'nos digas por cada uno qué procede:<br/>'
            '&bull; <b>Se da de baja</b> &mdash; si ya no sirve, se desecha y se '
            'registra la merma.<br/>'
            '&bull; <b>Se revalida</b> &mdash; si Calidad puede extender la vida útil '
            'con un análisis, se documenta la extensión.<br/>'
            '&bull; <b>La fecha está mal</b> &mdash; si la etiqueta dice otra cosa o '
            'la capturamos mal, se corrige.<br/><br/>'
            'Mientras no se resuelva, cada lote queda registrado y marcado: no se '
            'pierde de vista, pero tampoco se usa sin que alguien lo autorice.<br/><br/>'
            'En el historial de cada lote dejamos la misma nota con su detalle, por '
            'si prefieres revisarlos uno por uno desde Inventario.<br/><br/>'
            '<i>Lo pidió Mery. Cualquier duda del registro, con Desarrollo.</i>'
        ) % {'marca': MARCA, 'lista': Markup(''.join(renglones))},
        message_type='comment',
        subtype_xmlid='mail.mt_comment')
    env.cr.commit()
    print('MANDADO por Discuss al canal %s (id %s)' % (canal.name or 'chat', canal.id))

print('-' * 92)
print('miembros del canal: %s' % ', '.join(canal.channel_member_ids.mapped('partner_id.name')))
print('mensajes en el canal: %d' % len(canal.message_ids))
print('-' * 92)
print('CONTENIDO ENVIADO:')
for l, cant, cad, dias in datos:
    est = 'vencido hace %d dias' % dias if dias > 0 else 'vence en %d dias' % abs(dias)
    print('   %-9s %-13s %8.2f %-3s %s   %s' % (
        l.product_id.default_code, l.name, cant, l.product_id.uom_id.name,
        cad.strftime('%d/%m/%Y') if cad else '-', est))
