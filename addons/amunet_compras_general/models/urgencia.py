# -*- coding: utf-8 -*-
"""Urgencia de una solicitud (compra y material).

Hasta hoy una solicitud no decia que tan urgente era, y la fecha requerida
era opcional: de 321 solicitudes solo 164 la traian llena. Sin esos dos
datos Compras no puede decidir el flete ni priorizar.

Regla acordada con Fernando: si la solicitud NO es normal, hay que decir
por que urge y para cuando se necesita. Las dos cosas son obligatorias.

El modulo solo AÑADE: las solicitudes historicas quedan en 'normal' y no
se tocan. Los constraints miran solo lo que se escribe de aqui en adelante,
porque 'normal' no exige nada.
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

URGENCIA_SELECTION = [
    ('normal', 'Normal'),
    ('urge', 'Urge'),
    ('linea_detenida', 'Para linea detenida'),
]

# Orden de severidad, para saber cual urgencia manda cuando una orden de
# compra viene de varias solicitudes.
URGENCIA_PESO = {'normal': 0, 'urge': 1, 'linea_detenida': 2}


class AmunetUrgenciaMixin(models.AbstractModel):
    """Los tres campos y sus dos reglas, compartidos por los dos modelos.

    Se hace como AbstractModel para no repetir el constraint: la regla de
    negocio es la misma en la solicitud de compra y en la de material.
    """

    _name = 'amunet.urgencia.mixin'
    _description = 'Urgencia de una solicitud'

    amunet_urgencia = fields.Selection(
        selection=URGENCIA_SELECTION,
        string='Urgencia',
        default='normal',
        required=True,
        tracking=True,
        help='Normal es el caso comun. "Urge" y "Para linea detenida" '
             'obligan a explicar el motivo y a poner fecha requerida.',
    )
    amunet_urgencia_motivo = fields.Char(
        string='Motivo de la urgencia',
        tracking=True,
        help='Por que no puede esperar. Obligatorio cuando la urgencia no '
             'es normal.',
    )

    @api.constrains('amunet_urgencia', 'amunet_urgencia_motivo')
    def _check_amunet_urgencia_motivo(self):
        for req in self:
            if req.amunet_urgencia == 'normal':
                continue
            if not (req.amunet_urgencia_motivo or '').strip():
                raise ValidationError(_(
                    'Marcaste la solicitud como "%s" pero no dijiste por que.\n\n'
                    'Escribe el motivo de la urgencia: Compras lo necesita para '
                    'decidir si vale la pena pagar un flete mas caro.'
                ) % dict(URGENCIA_SELECTION).get(req.amunet_urgencia))

    @api.constrains('amunet_urgencia', 'required_date')
    def _check_amunet_urgencia_fecha(self):
        for req in self:
            if req.amunet_urgencia == 'normal':
                continue
            if not req.required_date:
                raise ValidationError(_(
                    'Marcaste la solicitud como "%s" pero la dejaste sin fecha '
                    'requerida.\n\nCaptura para cuando se necesita: sin fecha no '
                    'hay forma de saber si la compra llego a tiempo.'
                ) % dict(URGENCIA_SELECTION).get(req.amunet_urgencia))


class AmunetSolicitudCompraUrgencia(models.Model):
    _name = 'amunet.solicitud.compra'
    _inherit = ['amunet.solicitud.compra', 'amunet.urgencia.mixin']


class AmunetMaterialRequestUrgencia(models.Model):
    _name = 'amunet.material.request'
    _inherit = ['amunet.material.request', 'amunet.urgencia.mixin']
