# -*- coding: utf-8 -*-
# Reinicio MENSUAL del consecutivo de los folios de producto (MMAA/NN/ABR).
# El folio lleva el mes/año en el prefijo, pero el numero (NN) debe reiniciar
# a 01 cada mes (PNOGE-014 / decision de Fernando 2026-07-13). Odoo no lo hace
# nativamente sin rangos por fecha (que reinician por AÑO), asi que se controla
# aqui: al pedir el siguiente folio, si cambio el mes desde el ultimo uso, se
# reinicia number_next a 1. Atomico dentro de la transaccion de creacion de la MO.
from odoo import models, fields


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    amunet_last_period = fields.Char(
        string='Último periodo (folio mensual)', copy=False,
        help='Mes+año (MMYYYY) del último folio generado; si cambia, el '
             'consecutivo reinicia a 1.')

    def _amunet_next_folio_mensual(self):
        """Devuelve el siguiente folio reiniciando el consecutivo a 1 cuando
        cambia el mes de elaboracion."""
        self.ensure_one()
        period = fields.Date.context_today(self).strftime('%m%Y')
        if self.amunet_last_period != period:
            self.sudo().write({'number_next': 1, 'amunet_last_period': period})
        return self.next_by_id()
