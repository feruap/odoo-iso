# -*- coding: utf-8 -*-
import base64
from odoo import http
from odoo.http import request


class AmunetFormatoController(http.Controller):

    @http.route('/amunet/formato/imprimir/<int:solicitud_id>', type='http', auth='user')
    def visor_impresion(self, solicitud_id, **kwargs):
        sol = request.env['amunet.documento.formato.solicitud'].browse(solicitud_id)
        if not sol.exists() or sol.state != 'aprobada':
            return request.not_found()
        es_manager = request.env.user.has_group('amunet_documentos.group_documentos_manager')
        if sol.solicitante_id.id != request.env.user.id and not es_manager:
            return request.not_found()
        if not sol.archivo:
            return request.not_found()

        html = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8"/>
    <title>Impresión controlada — {sol.formato_codigo}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ background: #525659; font-family: Arial, sans-serif; }}
        .barra {{
            background: #323639; color: #fff;
            padding: 10px 20px;
            display: flex; align-items: center; gap: 16px;
            height: 48px;
        }}
        .barra button {{
            background: #1a73e8; color: #fff; border: none;
            padding: 7px 18px; border-radius: 4px;
            cursor: pointer; font-size: 14px;
        }}
        .barra button:hover {{ background: #1558b0; }}
        .barra .sello {{
            font-size: 12px; opacity: 0.75;
            border-left: 1px solid #666; padding-left: 16px;
        }}
        embed {{
            display: block;
            width: 100%;
            height: calc(100vh - 48px);
        }}
        @media print {{
            .barra {{ display: none; }}
            embed {{ height: 100vh; }}
        }}
    </style>
</head>
<body>
    <div class="barra">
        <button onclick="window.print()">🖨️ Imprimir</button>
        <span class="sello">
            Copia no controlada &nbsp;|&nbsp;
            {sol.formato_codigo} — {sol.formato_nombre} &nbsp;|&nbsp;
            Solicitante: {sol.solicitante_id.name}
        </span>
    </div>
    <embed src="/amunet/formato/archivo/{sol.id}" type="application/pdf"/>
    <script>
        window.addEventListener('load', function() {{
            setTimeout(function() {{ window.print(); }}, 1200);
        }});
    </script>
</body>
</html>'''
        return request.make_response(html, headers=[('Content-Type', 'text/html; charset=utf-8')])

    @http.route('/amunet/formato/archivo/<int:solicitud_id>', type='http', auth='user')
    def servir_archivo(self, solicitud_id, **kwargs):
        sol = request.env['amunet.documento.formato.solicitud'].browse(solicitud_id)
        if not sol.exists() or sol.state != 'aprobada':
            return request.not_found()
        es_manager = request.env.user.has_group('amunet_documentos.group_documentos_manager')
        if sol.solicitante_id.id != request.env.user.id and not es_manager:
            return request.not_found()
        if not sol.archivo:
            return request.not_found()

        datos = base64.b64decode(sol.archivo)
        filename = sol.archivo_filename or 'formato.pdf'
        return request.make_response(datos, headers=[
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', f'inline; filename="{filename}"'),
            ('X-Content-Type-Options', 'nosniff'),
        ])
