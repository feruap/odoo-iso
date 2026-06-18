# -*- coding: utf-8 -*-
import calendar
from datetime import date, timedelta
from markupsafe import Markup
from odoo import models, fields, api, _

MESES = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
         'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
TURNOS = [(9.0, '9'), (13.0, '1'), (18.0, '6')]  # 9am, 1pm, 6pm


def _ini(name):
    if not name:
        return ''
    parts = [p for p in name.split() if p]
    return ''.join(p[0] for p in parts[:2]).upper()


class AmunetTempChartWizard(models.TransientModel):
    _name = 'amunet.temp.chart.wizard'
    _description = 'Generar grafica de control mensual de temperatura'

    area_id = fields.Many2one('amunet.temp.area', string='Área', required=True)
    year = fields.Selection(
        [(str(y), str(y)) for y in range(2024, 2031)], string='Año', required=True,
        default=lambda self: str(fields.Date.context_today(self).year))
    month = fields.Selection(
        [(str(i), MESES[i]) for i in range(1, 13)], string='Mes', required=True,
        default=lambda self: str(fields.Date.context_today(self).month))
    period_mode = fields.Selection(
        [('mes', 'Mes completo'), ('fraccion', 'Fracción (rango de fechas)')],
        string='Período', default='mes', required=True)
    date_from = fields.Date(string='Desde')
    date_to = fields.Date(string='Hasta')

    chart_html = fields.Html(
        string='Grafica', compute='_compute_chart_html', sanitize=False)

    @api.depends('area_id', 'month', 'year', 'period_mode', 'date_from', 'date_to')
    def _compute_chart_html(self):
        for w in self:
            if not w.area_id:
                w.chart_html = False
                continue
            h = w._header_vals()
            header = Markup(
                '<div style="text-align:center;margin:0 0 6px">'
                '<h4 style="margin:0">Formato de control de temperatura y humedad</h4>'
                '<div style="font-size:11px">Código: <strong>F-AL-008-001</strong></div>'
                '<div style="font-size:12px;margin-top:2px">'
                '<strong>Área:</strong> %s &nbsp;|&nbsp; '
                '<strong>No. Termohigrómetro:</strong> %s &nbsp;|&nbsp; '
                '<strong>Período:</strong> %s &nbsp;|&nbsp; '
                '<strong>Condiciones:</strong> %s</div></div>'
            ) % (h['area'], h['instrumento'], h['periodo'], h['cond'])
            w.chart_html = header + w.build_svg()

    def _chart_days(self):
        """Lista de fechas a graficar: mes completo o fraccion (rango)."""
        self.ensure_one()
        if self.period_mode == 'fraccion' and self.date_from and self.date_to:
            d0, d1 = sorted([self.date_from, self.date_to])
            n = max(1, min((d1 - d0).days + 1, 62))
            return [d0 + timedelta(days=i) for i in range(n)]
        year, month = int(self.year), int(self.month)
        ndays = calendar.monthrange(year, month)[1]
        return [date(year, month, d) for d in range(1, ndays + 1)]

    # datos para el encabezado del reporte
    def _header_vals(self):
        self.ensure_one()
        a = self.area_id
        cond = '%.0f-%.0f C, %.0f-%.0f %%HR' % (
            a.temp_min, a.temp_max, a.hum_min, a.hum_max)
        if self.period_mode == 'fraccion' and self.date_from and self.date_to:
            d0, d1 = sorted([self.date_from, self.date_to])
            periodo = '%s al %s' % (d0.strftime('%d/%m/%Y'), d1.strftime('%d/%m/%Y'))
        else:
            periodo = '%s %s' % (MESES[int(self.month)], self.year)
        return {
            'area': a.name,
            'instrumento': a.instrument_label or '-',
            'periodo': periodo,
            'cond': cond.replace('%%', '%'),
        }

    def action_print(self):
        self.ensure_one()
        return self.env.ref(
            'amunet_monitor_temperatura.action_report_temp_chart'
        ).report_action(self)

    # ------------------------------------------------------------------
    # Construccion del SVG (grafica de control, sin redondeo)
    # ------------------------------------------------------------------
    def build_svg(self):
        self.ensure_one()
        area = self.area_id
        days = self._chart_days()
        reads = self.env['amunet.temp.reading'].sudo().search([
            ('area_id', '=', area.id),
            ('date', '>=', days[0]),
            ('date', '<=', days[-1]),
            ('state', 'in', ('captured', 'deviation')),
        ])
        bykey = {}
        for r in reads:
            bykey[(r.date, round(r.scheduled_time, 2))] = r

        # --- geometria ---
        L = 64            # margen izquierdo (etiquetas eje Y)
        colw = 15         # ancho de columna (1 turno)
        ncols = len(days) * 3
        cw = ncols * colw
        W = L + cw + 16

        # eje temperatura
        t_lo, t_hi = 14.0, 31.0
        t_ppd = 12        # px por grado
        t_top = 26
        t_h = (t_hi - t_lo) * t_ppd

        def xcol(idx, ti):
            return L + (idx * 3 + ti) * colw + colw / 2.0

        def ytemp(t):
            t = max(t_lo, min(t_hi, t))
            return t_top + (t_hi - t) * t_ppd

        s = []
        s.append('<text x="%d" y="16" font-size="11" font-weight="bold">TEMPERATURA °C  (límites %.0f - %.0f)</text>' % (L, area.temp_min, area.temp_max))

        # cuadricula horizontal temp (cada 0.5) + etiquetas en enteros
        t = t_lo
        while t <= t_hi + 0.001:
            y = ytemp(t)
            major = abs(t - round(t)) < 0.01
            color = '#cfcfcf' if major else '#ececec'
            s.append('<line x1="%d" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="0.5"/>' % (L, y, L + cw, y, color))
            if major:
                s.append('<text x="%d" y="%.1f" font-size="8" text-anchor="end">%d</text>' % (L - 4, y + 3, int(round(t))))
            t += 0.5
        # lineas de limite (rojo)
        for lim in (area.temp_min, area.temp_max):
            if t_lo <= lim <= t_hi:
                y = ytemp(lim)
                s.append('<line x1="%d" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#d33" stroke-width="1"/>' % (L, y, L + cw, y))

        # cuadricula vertical (dia/turno)
        for idx in range(len(days)):
            for ti in range(3):
                x = L + (idx * 3 + ti) * colw
                col = '#bbb' if ti == 0 else '#eee'
                s.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="0.5"/>' % (x, t_top, x, t_top + t_h, col))
        s.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%.1f" stroke="#bbb" stroke-width="0.5"/>' % (L + cw, t_top, L + cw, t_top + t_h))

        # puntos temp + linea de union por dia
        pts = []
        for idx, d in enumerate(days):
            for ti, (th, _lbl) in enumerate(TURNOS):
                r = bykey.get((d, th))
                if r and r.temp_value:
                    pts.append((xcol(idx, ti), ytemp(r.temp_value), r.out_of_range))
        if len(pts) > 1:
            poly = ' '.join('%.1f,%.1f' % (p[0], p[1]) for p in pts)
            s.append('<polyline points="%s" fill="none" stroke="#3a6ea5" stroke-width="0.7"/>' % poly)
        for x, y, oor in pts:
            col = '#d33' if oor else '#1f4e79'
            s.append('<circle cx="%.1f" cy="%.1f" r="2.1" fill="%s"/>' % (x, y, col))

        # --- filas HORA / FECHA ---
        row_y = t_top + t_h
        def band(label, getter, yoff):
            yy = row_y + yoff
            s.append('<text x="%d" y="%.1f" font-size="7" text-anchor="end" font-weight="bold">%s</text>' % (L - 4, yy + 8, label))
            for idx, d in enumerate(days):
                for ti, (th, lbl) in enumerate(TURNOS):
                    x = L + (idx * 3 + ti) * colw
                    s.append('<rect x="%.1f" y="%.1f" width="%d" height="11" fill="none" stroke="#ddd" stroke-width="0.4"/>' % (x, yy, colw))
                    val = getter(d, th, ti, lbl)
                    if val:
                        s.append('<text x="%.1f" y="%.1f" font-size="6" text-anchor="middle">%s</text>' % (x + colw / 2.0, yy + 8, val))
        band('HORA', lambda d, th, ti, lbl: lbl, 0)
        band('FECHA', lambda d, th, ti, lbl: str(d.day) if ti == 1 else '', 12)

        # --- cuadricula humedad ---
        h_top = row_y + 32
        h_lo, h_hi = 30.0, 75.0
        h_ppd = 3.2
        h_h = (h_hi - h_lo) * h_ppd
        def yhum(h):
            h = max(h_lo, min(h_hi, h))
            return h_top + (h_hi - h) * h_ppd
        s.append('<text x="%d" y="%.1f" font-size="11" font-weight="bold">HUMEDAD %%HR  (límites %.0f - %.0f)</text>' % (L, h_top - 8, area.hum_min, area.hum_max))
        hh = h_lo
        while hh <= h_hi + 0.001:
            y = yhum(hh)
            major = (int(hh) % 5 == 0)
            s.append('<line x1="%d" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="0.5"/>' % (L, y, L + cw, y, '#cfcfcf' if major else '#ececec'))
            if major:
                s.append('<text x="%d" y="%.1f" font-size="8" text-anchor="end">%d</text>' % (L - 4, y + 3, int(hh)))
            hh += 1
        for lim in (area.hum_min, area.hum_max):
            if h_lo <= lim <= h_hi:
                y = yhum(lim)
                s.append('<line x1="%d" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#d33" stroke-width="1"/>' % (L, y, L + cw, y))
        for idx in range(len(days)):
            for ti in range(3):
                x = L + (idx * 3 + ti) * colw
                s.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="0.5"/>' % (x, h_top, x, h_top + h_h, '#bbb' if ti == 0 else '#eee'))
        hpts = []
        for idx, d in enumerate(days):
            for ti, (th, _l) in enumerate(TURNOS):
                r = bykey.get((d, th))
                if r and r.hum_required and r.hum_value:
                    hpts.append((xcol(idx, ti), yhum(r.hum_value)))
        if len(hpts) > 1:
            s.append('<polyline points="%s" fill="none" stroke="#3a6ea5" stroke-width="0.7"/>' % ' '.join('%.1f,%.1f' % p for p in hpts))
        for x, y in hpts:
            s.append('<circle cx="%.1f" cy="%.1f" r="2.1" fill="#1f4e79"/>' % (x, y))

        H = h_top + h_h + 20
        # width/height explicitos (px): wkhtmltopdf no pinta SVG con style width:100%.
        # Se escala para caber en la hoja apaisada (max ~1040px de ancho).
        max_w = 1040.0
        scale = min(1.0, max_w / float(W))
        disp_w = int(round(W * scale))
        disp_h = int(round(H * scale))
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" '
               'width="%d" height="%d" viewBox="0 0 %d %d" '
               'font-family="Arial">%s</svg>') % (disp_w, disp_h, W, H, ''.join(s))
        return Markup(svg)
