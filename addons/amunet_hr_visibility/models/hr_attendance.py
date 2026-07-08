import pytz
from datetime import datetime, date, timedelta
import calendar
from odoo import models, api

TOLERANCIA_MIN = 15     # minutos de tolerancia antes de marcar retardo
TZ = 'America/Mexico_City'


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    @api.model
    def _cron_cerrar_asistencias_abiertas(self):
        tz = pytz.timezone(TZ)
        now_local = datetime.now(tz)
        checkout_local = now_local.replace(hour=18, minute=0, second=0, microsecond=0)
        checkout_utc = checkout_local.astimezone(pytz.utc).replace(tzinfo=None)

        open_records = self.search([
            ('check_out', '=', False),
            ('check_in', '<', checkout_utc),
        ])
        if open_records:
            open_records.write({'check_out': checkout_utc})

    @api.model
    def _cron_reporte_ausencias_quincena(self):
        tz = pytz.timezone(TZ)
        hoy = datetime.now(tz).date()

        if hoy.day == 16:
            fecha_ini = date(hoy.year, hoy.month, 1)
            fecha_fin = date(hoy.year, hoy.month, 15)
            label = '1 al 15 de %s %d' % (hoy.strftime('%B'), hoy.year)
        elif hoy.day == 1:
            mes_ant = hoy.month - 1 if hoy.month > 1 else 12
            anio_ant = hoy.year if hoy.month > 1 else hoy.year - 1
            ultimo_dia = calendar.monthrange(anio_ant, mes_ant)[1]
            fecha_ini = date(anio_ant, mes_ant, 16)
            fecha_fin = date(anio_ant, mes_ant, ultimo_dia)
            label = '16 al %d de %s %d' % (
                ultimo_dia, datetime(anio_ant, mes_ant, 1).strftime('%B'), anio_ant)
        else:
            return

        # Días hábiles del período (lunes a viernes), excluyendo festivos oficiales
        festivos = set()
        hojas_festivas = self.env['resource.calendar.leaves'].search([
            ('resource_id', '=', False),
            ('holiday_id', '=', False),
            ('date_from', '<=', str(fecha_fin)),
            ('date_to', '>=', str(fecha_ini)),
        ])
        for hoja in hojas_festivas:
            d = max(hoja.date_from.date(), fecha_ini)
            while d <= min(hoja.date_to.date(), fecha_fin):
                festivos.add(d)
                d += timedelta(days=1)

        dias_habiles = [
            fecha_ini + timedelta(days=i)
            for i in range((fecha_fin - fecha_ini).days + 1)
            if (fecha_ini + timedelta(days=i)).weekday() < 5
            and (fecha_ini + timedelta(days=i)) not in festivos
        ]
        if not dias_habiles:
            return

        empleados = self.env['hr.employee'].search([
            ('active', '=', True),
            ('user_id', '!=', False),
            ('name', 'not ilike', 'Practicante'),
            ('name', 'not ilike', 'Administrator'),
        ])

        permisos = self.env['hr.leave'].search([
            ('state', '=', 'validate'),
            ('date_from', '<=', str(fecha_fin)),
            ('date_to', '>=', str(fecha_ini)),
        ])

        ausencias_filas = []
        retardos_filas = []

        for emp in sorted(empleados, key=lambda e: e.name):
            dias_permiso = set()
            for p in permisos.filtered(lambda l: l.employee_id == emp):
                d = max(p.date_from.date(), fecha_ini)
                while d <= min(p.date_to.date(), fecha_fin):
                    if d.weekday() < 5:
                        dias_permiso.add(d)
                    d += timedelta(days=1)

            registros = self.search([
                ('employee_id', '=', emp.id),
                ('date', '>=', str(fecha_ini)),
                ('date', '<=', str(fecha_fin)),
            ])

            dias_con_asistencia = set(registros.mapped('date'))

            # Ausencias
            ausencias = [
                d for d in dias_habiles
                if d not in dias_con_asistencia and d not in dias_permiso
            ]
            if ausencias:
                ausencias_filas.append((emp.name, ausencias))

            # Hora de entrada según el calendario del empleado (por día de semana)
            cal = emp.resource_id.calendar_id
            hora_entrada_por_dow = {}
            for line in cal.attendance_ids:
                dow = int(line.dayofweek)
                if dow not in hora_entrada_por_dow or line.hour_from < hora_entrada_por_dow[dow]:
                    hora_entrada_por_dow[dow] = line.hour_from  # e.g. 9.0 o 13.0

            # Retardos: check_in después de hora_entrada + tolerancia
            retardos = []
            for rec in registros:
                if not rec.check_in:
                    continue
                dow = rec.date.weekday()
                hora_entrada = hora_entrada_por_dow.get(dow)
                if hora_entrada is None:
                    continue
                limite_min = hora_entrada * 60 + TOLERANCIA_MIN
                check_in_local = pytz.utc.localize(rec.check_in).astimezone(pytz.timezone(TZ))
                check_in_min = check_in_local.hour * 60 + check_in_local.minute
                if check_in_min > limite_min:
                    minutos_tarde = check_in_min - int(hora_entrada * 60)
                    retardos.append((rec.date, check_in_local.strftime('%H:%M'), minutos_tarde))
            if retardos:
                retardos_filas.append((emp.name, sorted(retardos, key=lambda x: x[0])))

        if not ausencias_filas and not retardos_filas:
            return

        # ── Construir correo ──────────────────────────────────────────────
        html = ['<p>Hola Patricia,</p>',
                '<p>Aquí el resumen del período <b>%s</b>:</p>' % label]

        # Sección 1: Ausencias
        html.append('<h3 style="color:#c0392b;">Ausencias sin registro</h3>')
        if ausencias_filas:
            html.append('<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;margin-bottom:16px;">')
            html.append('<tr style="background:#f5b7b1"><th>Empleado</th><th>Días ausentes</th><th>Total</th></tr>')
            for nombre, ausencias in ausencias_filas:
                dias_str = ', '.join(d.strftime('%d/%m') for d in sorted(ausencias))
                html.append('<tr><td>%s</td><td>%s</td><td align="center">%d</td></tr>' % (nombre, dias_str, len(ausencias)))
            html.append('</table>')
            html.append('<p style="font-size:12px;">Si aplica descuento, agrégalo en el recibo con el concepto <b>FALTA</b>.</p>')
        else:
            html.append('<p>✅ Sin ausencias en este período.</p>')

        # Sección 2: Retardos
        html.append('<h3 style="color:#e67e22;">Retardos (entrada después de 9:15 AM)</h3>')
        if retardos_filas:
            html.append('<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;margin-bottom:16px;">')
            html.append('<tr style="background:#fad7a0"><th>Empleado</th><th>Fecha</th><th>Hora entrada</th><th>Min. tarde</th></tr>')
            for nombre, retardos in retardos_filas:
                for i, (dia, hora, minutos) in enumerate(retardos):
                    celda_nombre = ('<td rowspan="%d"><b>%s</b><br/><small>%d retardo(s)</small></td>' % (len(retardos), nombre, len(retardos))) if i == 0 else ''
                    html.append('<tr>%s<td>%s</td><td>%s</td><td align="center">%d min</td></tr>' % (
                        celda_nombre, dia.strftime('%d/%m/%Y'), hora, minutos))
            html.append('</table>')
            html.append('<p style="font-size:12px;">Revisa el acumulado por persona para determinar si aplica descuento vía nómina.</p>')
        else:
            html.append('<p>✅ Sin retardos en este período.</p>')

        html.append('<p>Saludos,<br/>Sistema Odoo — RRHH</p>')

        self.env['mail.mail'].create({
            'subject': 'Asistencias quincena %s — ausencias y retardos' % label,
            'email_to': 'rrhh@amunet.com.mx',
            'body_html': '\n'.join(html),
            'auto_delete': True,
        }).send()
