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

    def _amunet_devolver_folio(self, folio):
        """Devuelve el consecutivo si `folio` fue el ULTIMO que emitio esta
        secuencia. Solo entonces: si ya se emitieron folios despues, retroceder
        haria que dos ordenes acabaran con el mismo numero.

        Se usa cuando una orden se borra o se cancela sin haberse trabajado. Sin
        esto, una orden creada por equivocacion quema su folio para siempre y el
        siguiente producto arranca en 02 aunque sea el primero del mes -- paso el
        3-sep-2026, cuando se cancelaron diez ordenes en el mismo minuto y varios
        productos quedaron corridos. Pedido por Mery, 23-sep-2026.

        Devuelve True si de verdad lo regreso.
        """
        self.ensure_one()
        if not folio:
            return False
        try:
            prefix, suffix = self._get_prefix_suffix()
        except Exception:
            prefix, suffix = (self.prefix or ''), (self.suffix or '')
        prefix = prefix or ''
        suffix = suffix or ''
        if not folio.startswith(prefix):
            return False
        medio = folio[len(prefix):]
        if suffix:
            if not medio.endswith(suffix):
                return False
            medio = medio[:-len(suffix)]
        if not medio.isdigit():
            return False
        numero = int(medio)
        # El contador apunta al SIGUIENTE por emitir: si el folio que se va es
        # el anterior, es el ultimo emitido y se puede regresar.
        if self.number_next_actual != numero + 1:
            return False
        self.sudo().write({'number_next': numero})
        return True

