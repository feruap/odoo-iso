# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AmunetRegistroAlertas(models.Model):
    """Acciones programadas: alerta de vencimiento y reporte mensual."""
    _inherit = 'amunet.registro.capacitacion'

    @api.model
    def _get_gestores_capacitacion(self):
        grupo = self.env.ref('amunet_competencias.group_competencias_manager', False)
        if not grupo:
            return self.env['res.users']
        return grupo.sudo().users.filtered('active')

    @api.model
    def _enviar_correo(self, asunto, html, destinatarios):
        Mail = self.env['mail.mail'].sudo()
        partner_ids = [u.partner_id.id for u in destinatarios
                       if u.partner_id and u.partner_id.email]
        if not partner_ids:
            _logger.warning("No hay destinatarios con email; no se envia el correo.")
            return False
        mail = Mail.create({
            'subject': asunto,
            'body_html': html,
            'recipient_ids': [(6, 0, partner_ids)],
            'auto_delete': True,
        })
        mail.send()
        return mail

    @api.model
    def _cron_alerta_vencimiento(self, dias=30):
        """Aviso al Gestor de Capacitacion de registros que vencen en <=dias dias."""
        limite = fields.Date.today() + timedelta(days=dias)
        proximos = self.sudo().search([
            ('state', 'in', ('vigente', 'proxima')),
            ('expiry_date', '>=', fields.Date.today()),
            ('expiry_date', '<=', limite),
        ], order='expiry_date asc')
        if not proximos:
            _logger.info("Alerta vencimiento: sin registros por vencer en %d dias.", dias)
            return True
        managers = self._get_gestores_capacitacion()
        if not managers:
            return True
        filas = []
        for r in proximos:
            scope = r.procedure_id.code if r.procedure_id else (
                r.parameter_id.name if r.parameter_id else '-')
            filas.append(
                "<tr><td style='padding:5px;border-bottom:1px solid #ccc;'>%s</td>"
                "<td style='padding:5px;border-bottom:1px solid #ccc;'>%s</td>"
                "<td style='padding:5px;border-bottom:1px solid #ccc;'>%s</td></tr>" % (
                    (r.user_id.name or ''), scope, r.expiry_date))
        html = (
            "<div style='font-family:Arial,sans-serif;font-size:13px;color:#333;'>"
            "<p>Hola,</p>"
            "<p>El sistema detectó <strong>%d</strong> registro(s) de capacitación "
            "que vencerán en los próximos <strong>%d</strong> días.</p>"
            "<table style='width:100%%;border-collapse:collapse;margin-top:10px;'>"
            "<thead><tr style='background:#1F3864;color:#FFF;'>"
            "<th style='padding:6px;text-align:left;'>Empleado</th>"
            "<th style='padding:6px;text-align:left;'>PNO / SOP</th>"
            "<th style='padding:6px;text-align:left;'>Vence</th>"
            "</tr></thead><tbody>%s</tbody></table>"
            "<p style='margin-top:14px;'>Programa las renovaciones correspondientes.</p>"
            "<p style='color:#888;font-size:11px;'>Mensaje automático — Amunet ISO 13485 §6.2.</p>"
            "</div>" % (len(proximos), dias, ''.join(filas)))
        self._enviar_correo(
            "Capacitaciones por vencer en %d días" % dias, html, managers)
        _logger.info("Alerta vencimiento: %d registros notificados.", len(proximos))
        return True

    @api.model
    def _cron_reporte_mensual(self):
        """Reporte mensual al Gestor: estado de cumplimiento."""
        v = self.sudo().search_count([('state', '=', 'vigente')])
        p = self.sudo().search_count([('state', '=', 'proxima')])
        x = self.sudo().search_count([('state', '=', 'vencida')])
        c = self.sudo().search_count([('state', '=', 'cancelada')])
        managers = self._get_gestores_capacitacion()
        if not managers:
            return True
        html = (
            "<div style='font-family:Arial,sans-serif;font-size:13px;color:#333;'>"
            "<p>Hola,</p>"
            "<p>Estado de las capacitaciones al <strong>%s</strong>:</p>"
            "<table style='width:100%%;border-collapse:collapse;margin-top:10px;'>"
            "<tr><td style='padding:6px;background:#EAF1FB;'><strong>Vigentes</strong></td>"
            "<td style='padding:6px;background:#E8F5E9;color:#2D7A2D;'>%d</td></tr>"
            "<tr><td style='padding:6px;background:#EAF1FB;'><strong>Por vencer</strong></td>"
            "<td style='padding:6px;background:#FFF8E1;color:#8A6D00;'>%d</td></tr>"
            "<tr><td style='padding:6px;background:#EAF1FB;'><strong>Vencidas</strong></td>"
            "<td style='padding:6px;background:#FFEBEE;color:#A12727;'>%d</td></tr>"
            "<tr><td style='padding:6px;background:#EAF1FB;'><strong>Canceladas</strong></td>"
            "<td style='padding:6px;background:#F5F5F5;color:#666;'>%d</td></tr>"
            "</table>"
            "<p style='margin-top:14px;'>Detalle: Competencias → Registros / Avance.</p>"
            "<p style='color:#888;font-size:11px;'>Reporte mensual automático — "
            "Amunet ISO 13485 §6.2.</p></div>"
            % (fields.Date.today(), v, p, x, c))
        self._enviar_correo(
            "Capacitación — Reporte mensual (%s)" % fields.Date.today(),
            html, managers)
        _logger.info("Reporte mensual enviado: vigente=%d proxima=%d vencida=%d", v, p, x)
        return True
