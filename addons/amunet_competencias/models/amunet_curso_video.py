# -*- coding: utf-8 -*-
import re
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AmunetCursoVideo(models.Model):
    """
    Video de un curso. Un curso puede tener varios videos en orden.
    Genera un reproductor embebido para que se vea dentro de la pagina,
    sin descargar ni salir del sistema.
    """
    _name = 'amunet.curso.video'
    _description = 'Video de un Curso de Capacitacion'
    _order = 'curso_id, secuencia, id'

    curso_id = fields.Many2one(
        'amunet.curso', string='Curso', required=True, ondelete='cascade')
    secuencia = fields.Integer(string='Orden', default=10)
    name = fields.Char(string='Titulo del video', required=True)
    video_url = fields.Char(
        string='Enlace del video',
        help='URL de YouTube o Vimeo (se reproduce embebido), o cualquier otro enlace.')
    video_file = fields.Binary(string='Archivo de video', attachment=True)
    video_filename = fields.Char(string='Nombre del archivo')
    descripcion = fields.Text(string='Notas del video')

    embed_html = fields.Html(
        string='Reproductor', compute='_compute_embed_html',
        sanitize=False, readonly=True,
        help='Reproductor embebido generado automaticamente.')

    @api.depends('video_url', 'video_file', 'video_filename')
    def _compute_embed_html(self):
        for video in self:
            video.embed_html = video._build_embed()

    def _build_embed(self):
        """Construye el HTML del reproductor segun el tipo de fuente."""
        self.ensure_one()
        url = (self.video_url or '').strip()
        wrap_open = ('<div style="position:relative;padding-bottom:56.25%;'
                     'height:0;overflow:hidden;max-width:800px;">')
        wrap_close = '</div>'
        iframe_style = ('position:absolute;top:0;left:0;width:100%;height:100%;')

        # 1. YouTube
        yt = self._extract_youtube_id(url)
        if yt:
            return (
                f'{wrap_open}<iframe style="{iframe_style}" '
                f'src="https://www.youtube.com/embed/{yt}" frameborder="0" '
                f'allow="accelerometer;autoplay;clipboard-write;encrypted-media;'
                f'gyroscope;picture-in-picture" allowfullscreen></iframe>{wrap_close}'
            )

        # 2. Vimeo
        vm = self._extract_vimeo_id(url)
        if vm:
            return (
                f'{wrap_open}<iframe style="{iframe_style}" '
                f'src="https://player.vimeo.com/video/{vm}" frameborder="0" '
                f'allow="autoplay;fullscreen;picture-in-picture" '
                f'allowfullscreen></iframe>{wrap_close}'
            )

        # 3. Archivo de video subido
        if self.video_file and isinstance(self.id, int):
            attachment = self.env['ir.attachment'].sudo().search([
                ('res_model', '=', 'amunet.curso.video'),
                ('res_field', '=', 'video_file'),
                ('res_id', '=', self.id),
            ], limit=1)
            if attachment:
                return (
                    f'<video controls preload="metadata" '
                    f'style="width:100%;max-width:800px;max-height:450px;">'
                    f'<source src="/web/content/{attachment.id}"/>'
                    f'Tu navegador no puede reproducir este video.</video>'
                )

        # 4. Cualquier otro enlace
        if url:
            return (f'<a href="{url}" target="_blank" rel="noopener">'
                    f'Abrir el video en una pestana nueva</a>')

        return '<p style="color:#888;">Sin video configurado.</p>'

    @staticmethod
    def _extract_youtube_id(url):
        if not url:
            return False
        patterns = [
            r'(?:youtube\.com/watch\?(?:.*&)?v=)([A-Za-z0-9_-]{11})',
            r'(?:youtu\.be/)([A-Za-z0-9_-]{11})',
            r'(?:youtube\.com/embed/)([A-Za-z0-9_-]{11})',
            r'(?:youtube\.com/shorts/)([A-Za-z0-9_-]{11})',
        ]
        for pat in patterns:
            m = re.search(pat, url)
            if m:
                return m.group(1)
        return False

    @staticmethod
    def _extract_vimeo_id(url):
        if not url:
            return False
        m = re.search(r'vimeo\.com/(?:video/)?(\d+)', url)
        return m.group(1) if m else False
