# -*- coding: utf-8 -*-
from urllib.parse import quote
from odoo import http, fields, _
from odoo.http import request


class AmunetLimpiezaController(http.Controller):

    @http.route(['/limpieza/qr'], type='http', auth='user', website=False)
    def qr_sheet(self, **kw):
        env = request.env
        base = env['ir.config_parameter'].sudo().get_param('web.base.url') or ''
        Item = env['amunet.limpieza.item'].sudo()
        areas = env['amunet.temp.area'].sudo().search([('active', '=', True)])
        items = []
        for a in areas:
            if Item.search_count([('area_id', '=', a.id)]):
                url = '%s/limpieza/area/%d' % (base, a.id)
                src = ('/report/barcode/?barcode_type=QR&value=%s&width=320&height=320'
                       % quote(url, safe=''))
                items.append({'name': a.name, 'url': url, 'qr_src': src})
        return request.render('amunet_limpieza.qr_sheet', {'items': items})

    def _check_pin(self, pin):
        """Valida el PIN del usuario logueado contra el sistema de firmas."""
        user = request.env.user
        plain = (pin or '').strip()
        if not plain:
            return False
        rec = request.env['amunet.quality.signature.pin'].sudo().search(
            [('user_id', '=', user.id)], limit=1)
        if rec and rec.check_pin(plain):
            return True
        emp = user.employee_id
        return bool(emp and emp.pin and plain == emp.pin.strip())

    def _render_area(self, area_id, msg=None, msg_type='info'):
        env = request.env
        area = env['amunet.temp.area'].sudo().browse(int(area_id))
        if not area.exists():
            return request.not_found()
        Tarea = env['amunet.limpieza.tarea']
        today = fields.Date.context_today(Tarea)
        tareas = Tarea.sudo().search([
            ('area_id', '=', area.id), ('date', '=', today)], order='surface')
        is_sup = area.amunet_user_is_supervisor(env.user)
        can_clean = env.user.has_group('amunet_limpieza.group_limpieza_user')
        sani_semana = Tarea._amunet_sanitizer_for_date(today, 'rotativo')
        return request.render('amunet_limpieza.area_page', {
            'area': area, 'tareas': tareas, 'today': today,
            'is_sup': is_sup, 'can_clean': can_clean, 'user': env.user,
            'sani_semana': sani_semana, 'msg': msg, 'msg_type': msg_type,
        })

    @http.route(['/limpieza/area/<int:area_id>'], type='http', auth='user', website=False)
    def area(self, area_id, msg=None, msg_type='info', **kw):
        return self._render_area(area_id, msg=msg, msg_type=msg_type)

    @http.route(['/limpieza/registrar'], type='http', auth='user',
                methods=['POST'], csrf=True)
    def registrar(self, tarea_id=None, mode=None, pin=None, **kw):
        env = request.env
        tarea = env['amunet.limpieza.tarea'].sudo().browse(int(tarea_id))
        if not tarea.exists():
            return request.not_found()
        area_id = tarea.area_id.id
        if not self._check_pin(pin):
            return self._render_area(area_id, msg=_('PIN incorrecto.'), msg_type='danger')
        try:
            if mode == 'limpie':
                if tarea.state == 'realizada':
                    return self._render_area(area_id, msg=_('Esa limpieza ya estaba registrada.'), msg_type='info')
                tarea.with_user(env.user)._apply_realizada()
                txt = _('¡Listo! Limpieza registrada.')
            elif mode == 'firmar':
                if not tarea.area_id.amunet_user_is_supervisor(env.user):
                    return self._render_area(area_id, msg=_('Solo el supervisor del área puede firmar.'), msg_type='danger')
                if tarea.state != 'realizada':
                    return self._render_area(area_id, msg=_('Primero el responsable debe registrar la limpieza.'), msg_type='danger')
                tarea.with_user(env.user)._apply_supervision()
                txt = _('Supervisión firmada.')
            else:
                txt = ''
        except Exception as e:
            return self._render_area(area_id, msg=str(e), msg_type='danger')
        return self._render_area(area_id, msg=txt, msg_type='success')
