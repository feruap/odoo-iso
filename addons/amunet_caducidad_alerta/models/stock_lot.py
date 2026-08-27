# -*- coding: utf-8 -*-
from datetime import date

from odoo import models, fields, api, _

# Umbrales por defecto, en meses. Se pueden ajustar por parametro del sistema
# sin tocar codigo (Ajustes > Tecnico > Parametros del sistema).
UMBRAL_CORTA = 'amunet_caducidad.meses_corta'        # por debajo de esto: caducidad corta
UMBRAL_CORTESIA = 'amunet_caducidad.meses_cortesia'  # por debajo de esto: cortesia
UMBRAL_RETIRO = 'amunet_caducidad.meses_retiro'      # por debajo de esto: retirar

DEFAULTS = {UMBRAL_CORTA: 6, UMBRAL_CORTESIA: 4, UMBRAL_RETIRO: 2}


class StockLot(models.Model):
    _inherit = 'stock.lot'

    amunet_condicion_caducidad = fields.Selection([
        ('normal', 'Normal'),
        ('corta', 'Caducidad corta'),
        ('cortesia', 'Cortesia'),
        ('retirar', 'Retirar'),
        ('vencido', 'Vencido'),
        ('sin_fecha', 'Sin fecha de caducidad'),
    ], string='Condicion por caducidad', default='sin_fecha', readonly=True,
        index=True, copy=False, tracking=True,
        help='En que condicion comercial esta el lote segun lo que le queda de vida. '
             'Lo recalcula un proceso diario.')

    amunet_dias_caducidad = fields.Integer(
        string='Dias para caducar', readonly=True, copy=False,
        help='Dias que faltan para la fecha de caducidad. Negativo si ya paso.')

    amunet_caducidad_revisada = fields.Date(
        string='Semaforo actualizado el', readonly=True, copy=False)

    # ------------------------------------------------------------------
    @api.model
    def _amunet_umbrales(self):
        """Umbrales en meses, leidos de parametros del sistema."""
        param = self.env['ir.config_parameter'].sudo()
        valores = {}
        for clave, defecto in DEFAULTS.items():
            try:
                valores[clave] = int(param.get_param(clave, defecto))
            except (TypeError, ValueError):
                valores[clave] = defecto
        return valores

    @api.model
    def _amunet_condicion(self, fecha_caducidad, hoy=None):
        """Condicion comercial de una fecha de caducidad. Funcion pura."""
        if not fecha_caducidad:
            return 'sin_fecha', 0
        hoy = hoy or fields.Date.context_today(self)
        if hasattr(fecha_caducidad, 'date'):
            fecha_caducidad = fecha_caducidad.date()
        dias = (fecha_caducidad - hoy).days
        if dias < 0:
            return 'vencido', dias
        u = self._amunet_umbrales()
        meses = dias / 30.0
        if meses < u[UMBRAL_RETIRO]:
            return 'retirar', dias
        if meses < u[UMBRAL_CORTESIA]:
            return 'cortesia', dias
        if meses < u[UMBRAL_CORTA]:
            return 'corta', dias
        return 'normal', dias

    def _amunet_recalcular_caducidad(self):
        """Escribe la condicion en cada lote. Solo toca lo que cambio."""
        hoy = fields.Date.context_today(self)
        for lote in self:
            condicion, dias = self._amunet_condicion(lote.expiration_date, hoy)
            valores = {}
            if lote.amunet_condicion_caducidad != condicion:
                valores['amunet_condicion_caducidad'] = condicion
            if lote.amunet_dias_caducidad != dias:
                valores['amunet_dias_caducidad'] = dias
            if lote.amunet_caducidad_revisada != hoy:
                valores['amunet_caducidad_revisada'] = hoy
            if valores:
                super(StockLot, lote).write(valores)
        return True

    @api.model
    def _cron_amunet_semaforo_caducidad(self):
        """Proceso diario: el tiempo pasa aunque nadie edite los lotes."""
        lotes = self.search([('expiration_date', '!=', False)])
        lotes._amunet_recalcular_caducidad()
        sin_fecha = self.search([
            ('expiration_date', '=', False),
            ('amunet_condicion_caducidad', '!=', 'sin_fecha'),
        ])
        if sin_fecha:
            sin_fecha._amunet_recalcular_caducidad()
        return True

    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        lotes = super().create(vals_list)
        lotes._amunet_recalcular_caducidad()
        return lotes

    def write(self, vals):
        res = super().write(vals)
        if 'expiration_date' in vals:
            self._amunet_recalcular_caducidad()
        return res
