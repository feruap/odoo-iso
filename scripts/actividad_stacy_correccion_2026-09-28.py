# -*- coding: utf-8 -*-
"""El punto 1 de la actividad de Stacy quedo sin efecto.

Decia que faltaba SPSAN01 en la lista. No falta: Documentacion renombro
SPSPC01 -> SPSCA29 y SPSAN01 -> SPSCA30 para dejar una sola serie, y con el
nombre nuevo si esta. Verificado: las 30 de captura estan las 30.
"""
from markupsafe import Markup

act = env['mail.activity'].browse(4300)
assert act.exists(), 'No existe la actividad 4300'

act.note = Markup(
    '<p>Revisar el catálogo <b>amunet.clave</b> (Lista Maestra de Claves) contra los '
    'productos que existen de verdad en Odoo.</p>'
    '<p><b>Cuando algo no coincida, manda lo que está dado de alta en Odoo.</b> '
    'La lista se ajusta al sistema, no al revés. Si crees que Odoo es el que está mal, '
    '<b>pregunta antes de cambiar nada</b> — no corrijas el producto por tu cuenta.</p>'
    '<p><b>Corrección:</b> el primer punto que te puse (que faltaba SPSAN01) ya no '
    'aplica. Renombraron SPSPC01 a SPSCA29 y SPSAN01 a SPSCA30 para dejar una sola '
    'serie, y con la clave nueva sí está. Verificado: las 30 soluciones de captura '
    'están las 30 en tu lista.</p>'
    '<p>Quedan dos puntos:</p>'
    '<ol>'
    '<li><b>MPREC35 "Ácido cloroáurico" sigue como activa</b> en la lista, pero el '
    'producto se borró hoy en Odoo: el ácido cloroáurico quedó con una sola clave.</li>'
    '<li><b>46 claves de la lista no tienen producto en Odoo</b> — 27 semiprocesados, '
    '9 semiterminados, 5 materias primas, 4 terminados y 1 equipo. Hay que decidir una '
    'por una: o son claves reservadas que todavía no se dan de alta, o sobran.</li>'
    '</ol>'
    '<p>Para lo del punto 2 conviene mirar también <b>producción</b>, no solo staging: '
    'una clave puede existir allá y no aquí. Desarrollo ya te habilitó la consulta de '
    'lectura a la base productiva.</p>'
)
env.cr.commit()
print('actividad %s actualizada, vence %s, para %s' % (act.id, act.date_deadline, act.user_id.name))
