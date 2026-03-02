# -*- coding: utf-8 -*-
import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


class AmunetMatrizCompetencias(models.AbstractModel):
    """
    Servicio de validación de competencias.
    Modelo abstracto (sin tabla propia) que expone el método central
    de consulta: ¿Tiene este usuario capacitación vigente para este SOP?

    ISO 13485:2016 §6.2 — Competencia del personal.
    """
    _name = 'amunet.matriz.competencias'
    _description = 'Servicio de Validación de Competencias (ISO 13485 §6.2)'

    @api.model
    def verificar_competencia(self, user_id, procedure_id=None, parameter_id=None):
        """
        Retorna True si el usuario tiene AL MENOS UN registro de capacitación
        con estado 'vigente' para el par (SOP, Parámetro) dado.

        Lógica:
        - Si se proporciona procedure_id: busca match exacto por SOP.
        - Si se proporciona parameter_id: busca match exacto por Parámetro.
        - Si ambos se proporcionan: basta con que coincida cualquiera de los dos.
        - Si ninguno se proporciona: retorna True (sin alcance definido, no bloquear).

        :param user_id: int - ID del res.users
        :param procedure_id: int|None - ID del amunet.quality.procedure
        :param parameter_id: int|None - ID del amunet.quality.parameter
        :return: bool
        """
        if not procedure_id and not parameter_id:
            _logger.debug(
                "verificar_competencia: sin alcance definido para user %s, retorna True.",
                user_id
            )
            return True

        RegistroCapacitacion = self.env['amunet.registro.capacitacion']

        # Construir dominio base
        base_domain = [
            ('user_id', '=', user_id),
            ('state', '=', 'vigente'),
        ]

        # Buscar por SOP
        if procedure_id:
            result = RegistroCapacitacion.search(
                base_domain + [('procedure_id', '=', procedure_id)], limit=1
            )
            if result:
                _logger.debug(
                    "Competencia VÁLIDA: user=%s procedure=%s → CAP: %s",
                    user_id, procedure_id, result.name
                )
                return True

        # Buscar por Parámetro
        if parameter_id:
            result = RegistroCapacitacion.search(
                base_domain + [('parameter_id', '=', parameter_id)], limit=1
            )
            if result:
                _logger.debug(
                    "Competencia VÁLIDA: user=%s parameter=%s → CAP: %s",
                    user_id, parameter_id, result.name
                )
                return True

        _logger.warning(
            "Competencia INVÁLIDA o VENCIDA: user=%s procedure=%s parameter=%s",
            user_id, procedure_id, parameter_id
        )
        return False

    @api.model
    def get_resumen_usuario(self, user_id):
        """
        Retorna un resumen de capacitaciones por usuario para la vista Matriz.
        Usado por el controlador de la vista Kanban/List de Matriz.

        :return: dict {procedure_id: state, ...}
        """
        registros = self.env['amunet.registro.capacitacion'].search([
            ('user_id', '=', user_id),
        ])
        resumen = {}
        for r in registros:
            key = ('procedure', r.procedure_id.id) if r.procedure_id else ('parameter', r.parameter_id.id)
            # Conservar el estado más reciente (la búsqueda viene ordenada por expiry_date asc)
            resumen[key] = {
                'state': r.state,
                'expiry_date': r.expiry_date,
                'name': r.name,
            }
        return resumen
