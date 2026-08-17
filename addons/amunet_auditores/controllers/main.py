from odoo import fields, http
from odoo.http import request

_PAGE = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Convocatoria Auditores — Amunet</title>
  <style>
    body {{ font-family: Arial, sans-serif; background: #f5f5f5;
            display: flex; justify-content: center; align-items: center;
            min-height: 100vh; margin: 0; }}
    .card {{ background: #fff; border-radius: 10px; padding: 40px 48px;
             max-width: 480px; width: 100%%; box-shadow: 0 2px 12px rgba(0,0,0,.12); text-align: center; }}
    .icon {{ font-size: 3rem; margin-bottom: 12px; }}
    h2 {{ color: #333; margin: 0 0 12px; }}
    p  {{ color: #666; line-height: 1.5; }}
    .badge {{ display: inline-block; margin-top: 16px; padding: 6px 18px;
              border-radius: 20px; font-weight: bold; font-size: .9rem; }}
    .verde {{ background: #d4edda; color: #155724; }}
    .gris  {{ background: #e2e3e5; color: #383d41; }}
  </style>
</head>
<body><div class="card">{content}</div></body>
</html>"""


class AuditorConvocatoriaController(http.Controller):

    @http.route(
        '/auditores/respuesta/<string:token>/<string:respuesta>',
        type='http', auth='none', methods=['GET'], csrf=False,
    )
    def respuesta_invitacion(self, token, respuesta, **kwargs):
        env = request.env(user=1)  # sudo via uid=1

        inv = env['amunet.auditor.invitacion'].search(
            [('token', '=', token)], limit=1)

        if not inv:
            content = ('<div class="icon">❌</div>'
                       '<h2>Enlace no válido</h2>'
                       '<p>Este enlace no existe o ya venció.</p>')
            return request.make_response(
                _PAGE.format(content=content),
                headers=[('Content-Type', 'text/html; charset=utf-8')])

        conv = inv.convocatoria_id
        nombre = inv.usuario_id.name or 'Empleado'

        if inv.respuesta != 'pendiente':
            etiqueta = 'Interesado ✓' if inv.respuesta == 'interesado' else 'No interesado'
            clase = 'verde' if inv.respuesta == 'interesado' else 'gris'
            content = (f'<div class="icon">ℹ️</div>'
                       f'<h2>Ya registraste tu respuesta</h2>'
                       f'<p>Hola <b>{nombre}</b>, tu respuesta para la convocatoria '
                       f'<b>{conv.name}</b> ya fue registrada.</p>'
                       f'<span class="badge {clase}">{etiqueta}</span>')
            return request.make_response(
                _PAGE.format(content=content),
                headers=[('Content-Type', 'text/html; charset=utf-8')])

        if conv.state not in ('publicada', 'en_proceso'):
            content = ('<div class="icon">🔒</div>'
                       '<h2>Convocatoria cerrada</h2>'
                       '<p>Esta convocatoria ya no está activa.</p>')
            return request.make_response(
                _PAGE.format(content=content),
                headers=[('Content-Type', 'text/html; charset=utf-8')])

        now = fields.Datetime.now()

        if respuesta == 'si':
            candidato = env['amunet.auditor.candidato'].create({
                'convocatoria_id': conv.id,
                'usuario_id': inv.usuario_id.id,
            })
            inv.write({
                'respuesta': 'interesado',
                'fecha_respuesta': now,
                'candidato_id': candidato.id,
            })
            content = (f'<div class="icon">🎉</div>'
                       f'<h2>¡Gracias, {nombre}!</h2>'
                       f'<p>Quedaste registrado como candidato en la convocatoria '
                       f'<b>{conv.name}</b>. El equipo de Documentación '
                       f'se pondrá en contacto contigo.</p>'
                       f'<span class="badge verde">Interesado ✓</span>')

        elif respuesta == 'no':
            inv.write({'respuesta': 'no_interesado', 'fecha_respuesta': now})
            content = (f'<div class="icon">👍</div>'
                       f'<h2>Gracias por responder</h2>'
                       f'<p>Hola <b>{nombre}</b>, registramos que no participarás '
                       f'en la convocatoria <b>{conv.name}</b> esta vez. '
                       f'¡Quizá en la próxima!</p>'
                       f'<span class="badge gris">No interesado</span>')
        else:
            content = ('<div class="icon">❌</div><h2>Respuesta no reconocida</h2>'
                       '<p>Usa los botones del correo para responder.</p>')

        return request.make_response(
            _PAGE.format(content=content),
            headers=[('Content-Type', 'text/html; charset=utf-8')])
