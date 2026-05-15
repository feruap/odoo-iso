# -*- coding: utf-8 -*-
import logging
from odoo import models

_logger = logging.getLogger(__name__)


class AmunetQualityProcedure(models.Model):
    """
    Extension del PNO: cuando cambia la version de un procedimiento,
    marca los cursos vinculados como 'revision requerida'.
    ISO 13485:2016 - control de cambios y eficacia de la capacitacion.
    """
    _inherit = 'amunet.quality.procedure'

    def write(self, vals):
        version_cambia = 'version' in vals
        codigos_previos = {}
        if version_cambia:
            for proc in self:
                codigos_previos[proc.id] = proc.version
        res = super().write(vals)
        if version_cambia:
            cambiados = self.filtered(
                lambda p: codigos_previos.get(p.id) != p.version)
            if cambiados:
                Curso = self.env['amunet.curso'].sudo()
                cursos = Curso.search([('procedure_ids', 'in', cambiados.ids)])
                etiquetas = ', '.join(cambiados.mapped('code'))
                for curso in cursos:
                    curso.revision_requerida = True
                    curso.revision_motivo = (
                        'Cambio la version de un PNO vinculado: %s' % etiquetas)
                    curso.message_post(body=(
                        'Curso marcado para revision: cambio la version del '
                        'PNO %s. Revisar contenido y examen antes de seguir '
                        'usandolo.' % etiquetas))
                    _logger.info(
                        "Curso %s marcado para revision por cambio de version "
                        "en PNO(s) %s", curso.code, etiquetas)
        return res
