# -*- coding: utf-8 -*-
"""Actividad para Stacy: cotejar la Lista Maestra de Claves contra Odoo.

Se cuelga del PNOAL-005 "Asignacion de clave y lote interno", que es el
procedimiento que gobierna la asignacion de claves: es donde tiene sentido
que viva el pendiente, no en un registro suelto.
"""
from datetime import date, timedelta

from markupsafe import Markup

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
stacy = env['res.users'].search([('login', '=', 'documentacion@amunet.com.mx')], limit=1)
assert mery and stacy, 'Falta Mery o Stacy'
env = env(user=mery.id)

doc = env['amunet.documento'].search([('codigo', '=', 'PNOAL-005')], limit=1)
assert doc, 'No existe el PNOAL-005'
tipo = env.ref('mail.mail_activity_data_todo')
modelo = env['ir.model']._get('amunet.documento')

resumen = 'Cotejar la Lista Maestra de Claves contra lo dado de alta en Odoo'

# Si ya se creo una igual y sigue abierta, no se duplica.
ya = env['mail.activity'].search([
    ('res_model_id', '=', modelo.id), ('res_id', '=', doc.id),
    ('user_id', '=', stacy.id), ('summary', '=', resumen)], limit=1)

nota = Markup(
    '<p>Revisar el catálogo <b>amunet.clave</b> (Lista Maestra de Claves) contra los '
    'productos que existen de verdad en Odoo.</p>'
    '<p><b>Cuando algo no coincida, manda lo que está dado de alta en Odoo.</b> '
    'La lista se ajusta al sistema, no al revés. Si crees que Odoo es el que está mal, '
    '<b>pregunta antes de cambiar nada</b> — no corrijas el producto por tu cuenta.</p>'
    '<p>Ya cotejé la lista y salieron estos tres puntos concretos:</p>'
    '<ol>'
    '<li><b>Falta SPSAN01</b> "Solución de captura 25 (OH) D". Las otras 29 soluciones '
    'de captura que se dieron de alta hoy sí están; esa se quedó fuera.</li>'
    '<li><b>MPREC35 "Ácido cloroáurico" sigue como activa</b> en la lista, pero el '
    'producto se borró hoy en Odoo: el ácido cloroáurico quedó con una sola clave.</li>'
    '<li><b>46 claves de la lista no tienen producto en Odoo</b> — 27 semiprocesados, '
    '9 semiterminados, 5 materias primas, 4 terminados y 1 equipo. Hay que decidir una '
    'por una: o son claves reservadas que todavía no se dan de alta, o sobran.</li>'
    '</ol>'
    '<p>Para lo del punto 3 conviene mirar también <b>producción</b>, no solo staging: '
    'una clave puede existir allá y no aquí. Desarrollo ya te habilitó la consulta de '
    'lectura a la base productiva.</p>'
)

if ya:
    ya.write({'note': nota})
    print('Actividad ya existia (id %s), se actualizo la nota' % ya.id)
else:
    act = env['mail.activity'].create({
        'res_model_id': modelo.id, 'res_id': doc.id,
        'activity_type_id': tipo.id, 'summary': resumen,
        'user_id': stacy.id,
        'date_deadline': date.today() + timedelta(days=2),
        'note': nota,
    })
    print('Actividad creada id=%s para %s, vence %s' % (act.id, stacy.name, act.date_deadline))

env.cr.commit()
print('anclada en %s - %s' % (doc.codigo, doc.name))
