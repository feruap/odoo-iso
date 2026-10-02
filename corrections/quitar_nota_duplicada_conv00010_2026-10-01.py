# -*- coding: utf-8 -*-
"""Quitar la nota que duplique en CONV/00010.

QUE PASO. El 1-oct-2026 asente en el chatter de CONV/00010 una "Aclaracion de
trazabilidad" explicando que el combo recibido fue I163-4045 (4 hojas) y no
I204-4025 (3 hojas) que quedo capturado.

**Ya habia una nota del 29-sep-2026 que decia lo mismo, y mejor.** La del 29
precisa algo que la mia no dice: **el error estuvo en el PEDIDO P00214**, no en la
entrega -- se pidio el combo de 3 hojas y llego el de 4, que es el que la receta
del Combo Mosquito (DMDCZ01) necesita --, y que **Mery acepto el material como
llego**.

MI ERROR: reconstrui el analisis desde cero sin leer primero el historial del
documento. Mery me lo dijo en su momento -- "eso ya se reviso, tu me dijiste que no
se proponia el cambio del combo, revisa" -- y eso era justo lo que habia que
encontrar.

POR QUE SE QUITA. Dos aclaraciones del mismo hecho con fechas distintas invitan a
preguntar cual es la buena. La del 29 es la original, la mas precisa y la que esta
ligada a la decision que se tomo ese dia. Se queda esa.

Autorizado por Mery el 1-oct-2026: "si, quita la tuya y deja la del 29".

NO SE DEJA NOTA DEL BORRADO en el documento: seria una tercera aclaracion sobre un
hecho que ya esta bien explicado. El registro del borrado es este script y su
commit.

Idempotente.
"""
DOCUMENTO = 'CONV/00010'
MARCA = 'Aclaracion de trazabilidad (1-oct-2026)'

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

p = env['stock.picking'].sudo().search([('name', '=', DOCUMENTO)], limit=1)
assert p, 'No existe %s' % DOCUMENTO

print('notas de trazabilidad en %s ANTES:' % DOCUMENTO)
candidatas = env['mail.message'].sudo().search([
    ('model', '=', 'stock.picking'), ('res_id', '=', p.id),
    ('body', 'like', 'Aclaracion de trazabilidad')], order='id')
for m in candidatas:
    print('   id=%-7s %s  %s  (%d caracteres)' % (
        m.id, str(m.date)[:16], m.author_id.name or '?', len(m.body or '')))

# solo la que lleva LA MARCA del 1-oct: la del 29 no la tiene
mias = candidatas.filtered(lambda m: MARCA in (m.body or ''))
if not mias:
    print('\nNo hay nota del 1-oct. Ya estaba quitada o nunca se puso.')
else:
    ids = mias.ids
    mias.unlink()
    env.cr.commit()
    print('\nQUITADA(S): %s' % ids)

print('\nnotas de trazabilidad en %s DESPUES:' % DOCUMENTO)
quedan = env['mail.message'].sudo().search([
    ('model', '=', 'stock.picking'), ('res_id', '=', p.id),
    ('body', 'like', 'Aclaracion de trazabilidad')], order='id')
for m in quedan:
    print('   id=%-7s %s  %s' % (m.id, str(m.date)[:16], m.author_id.name or '?'))
print('   total: %d' % len(quedan))
