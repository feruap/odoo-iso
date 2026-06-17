# -*- coding: utf-8 -*-
"""Controlador para la auto-asistencia por QR.

Cuando un participante escanea el QR proyectado por el ponente, llega a
`/training/attend/<course_id>`. Como `auth='user'`, Odoo lo obliga a
loguearse primero (Authelia + login Odoo). Despues, esta vista busca
el `hr.employee` vinculado a su usuario, marca su linea de asistencia
y calcula puntualidad.
"""
import logging

from odoo import http, fields, _
from odoo.http import request

_logger = logging.getLogger(__name__)


class TrainingAttendController(http.Controller):

    @http.route(
        '/training/attend/<int:course_id>',
        type='http', auth='user',
        website=False, csrf=False, methods=['GET'],
    )
    def attend(self, course_id, **kwargs):
        env = request.env
        course = env['hr.training.course'].sudo().browse(course_id)
        if not course.exists():
            return request.render(
                'amunet_hr_training.training_attend_error',
                {
                    'title': _('Capacitacion no encontrada'),
                    'message': _(
                        'La capacitacion solicitada no existe o fue '
                        'eliminada. Verifica el codigo QR con tu '
                        'ponente.'),
                    'course': False,
                },
            )

        employee = env.user.employee_id
        token = kwargs.get('token')
        try:
            success, message, on_time = course.sudo().register_qr_attendance(
                employee, token=token)
        except Exception:
            _logger.exception(
                'Fallo registrando auto-asistencia QR (curso=%s, user=%s)',
                course_id, env.user.id)
            return request.render(
                'amunet_hr_training.training_attend_error',
                {
                    'title': _('Error inesperado'),
                    'message': _(
                        'Ocurrio un error al registrar tu asistencia. '
                        'Intentalo de nuevo o avisa al ponente.'),
                    'course': course,
                },
            )

        if not success:
            return request.render(
                'amunet_hr_training.training_attend_error',
                {
                    'title': _('No se pudo registrar tu asistencia'),
                    'message': message,
                    'course': course,
                },
            )
        return request.render(
            'amunet_hr_training.training_attend_success',
            {
                'course': course,
                'employee': employee,
                'on_time': on_time,
            },
        )

    # ------------------------------------------------------------------
    # Confirmacion de ponente por magic link (sin login requerido)
    # ------------------------------------------------------------------

    @http.route(
        '/training/confirmar-ponente/<string:token>',
        type='http', auth='public',
        website=False, csrf=False, methods=['GET'],
    )
    def speaker_confirm_page(self, token, **kwargs):
        """Muestra la pagina de confirmacion al ponente (no requiere login)."""
        env = request.env
        course = env['hr.training.course'].sudo().search(
            [('speaker_confirm_token', '=', token)], limit=1)
        if not course:
            return request.render(
                'amunet_hr_training.speaker_confirm_error',
                {
                    'title': _('Enlace no valido'),
                    'message': _(
                        'Este enlace de confirmacion no es valido o ya fue '
                        'utilizado. Si necesitas confirmar tu participacion, '
                        'pide a Recursos Humanos que te envie un nuevo enlace.'),
                    'course': False,
                },
            )
        if course.speaker_confirmed:
            return request.render(
                'amunet_hr_training.speaker_confirm_success',
                {'course': course, 'already': True},
            )
        return request.render(
            'amunet_hr_training.speaker_confirm_page',
            {'course': course, 'token': token},
        )

    @http.route(
        '/training/confirmar-ponente/<string:token>/confirmar',
        type='http', auth='public',
        website=False, csrf=False, methods=['POST'],
    )
    def speaker_confirm_do(self, token, **kwargs):
        """Procesa la confirmacion del ponente al pulsar el boton."""
        env = request.env
        course = env['hr.training.course'].sudo().search(
            [('speaker_confirm_token', '=', token)], limit=1)
        if not course:
            return request.render(
                'amunet_hr_training.speaker_confirm_error',
                {
                    'title': _('Enlace no valido'),
                    'message': _(
                        'Este enlace ya no es valido o fue usado anteriormente. '
                        'Pide a Recursos Humanos que te envie uno nuevo.'),
                    'course': False,
                },
            )
        ok, msg = course._confirm_speaker_by_token(token)
        if ok:
            return request.render(
                'amunet_hr_training.speaker_confirm_success',
                {'course': course, 'already': False},
            )
        return request.render(
            'amunet_hr_training.speaker_confirm_error',
            {
                'title': _('No se pudo confirmar'),
                'message': msg,
                'course': course,
            },
        )
