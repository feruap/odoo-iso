# -*- coding: utf-8 -*-
from datetime import date

from odoo import models, fields, api, _

# Umbrales por defecto, en meses. Se pueden ajustar por parametro del sistema
# sin tocar codigo (Ajustes > Tecnico > Parametros del sistema).
UMBRAL_CORTA = 'amunet_caducidad.meses_corta'        # por debajo de esto: caducidad corta
UMBRAL_CORTESIA = 'amunet_caducidad.meses_cortesia'  # por debajo de esto: cortesia
UMBRAL_RETIRO = 'amunet_caducidad.meses_retiro'      # por debajo de esto: retirar

DEFAULTS = {UMBRAL_CORTA: 6, UMBRAL_CORTESIA: 4, UMBRAL_RETIRO: 2}

# Los anaqueles de promociones solo existen para producto terminado. Una materia
# prima con caducidad corta no se vende con descuento: se usa antes o se da de
# baja, y eso lo decide produccion, no almacen de producto terminado.
CATEGORIA_PT = 'Producto terminado'


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

    amunet_ubicacion_condicion = fields.Selection([
        ('normal', 'Anaquel normal'),
        ('corta', 'Anaquel de caducidad corta'),
        ('cortesia', 'Anaquel de cortesias'),
        ('retenido', 'Retenido por caducidad'),
        ('sin_stock', 'Sin existencia'),
    ], string='Donde esta hoy', default='sin_stock', readonly=True, index=True,
        copy=False,
        help='En que anaquel esta fisicamente el lote, segun sus existencias.')

    amunet_requiere_movimiento = fields.Boolean(
        string='Debe moverse', readonly=True, index=True, copy=False,
        help='La fecha de caducidad ya cambio la condicion del lote, pero la '
             'mercancia sigue en el anaquel anterior.')

    amunet_movimiento_fecha = fields.Datetime(
        string='Movido de anaquel el', readonly=True, copy=False,
        help='Cuando se confirmo por ultima vez que este lote se cambio de anaquel.')

    amunet_movimiento_usuario_id = fields.Many2one(
        'res.users', string='Movido por', readonly=True, copy=False,
        help='Quien confirmo el ultimo cambio de anaquel de este lote.')

    amunet_movimiento_picking_id = fields.Many2one(
        'stock.picking', string='Traslado del movimiento', readonly=True, copy=False,
        help='El documento de traslado interno que respalda el ultimo cambio de anaquel.')

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

    def _amunet_ubicaciones_promocion(self):
        """Ids de los anaqueles de promociones, si el modulo alcanzo a crearlos."""
        ref = self.env.ref
        corta = ref('amunet_caducidad_alerta.location_caducidad_corta',
                    raise_if_not_found=False)
        cortesia = ref('amunet_caducidad_alerta.location_cortesias',
                       raise_if_not_found=False)
        retenidos = ref('amunet_caducidad_alerta.location_retenidos',
                        raise_if_not_found=False)
        return corta, cortesia, retenidos

    def _amunet_donde_esta(self):
        """En que anaquel esta el lote hoy, segun donde tiene existencia."""
        self.ensure_one()
        corta, cortesia, retenidos = self._amunet_ubicaciones_promocion()
        quants = self.quant_ids.filtered(
            lambda q: q.location_id.usage == 'internal' and q.quantity > 0)
        if not quants:
            return 'sin_stock'
        ubicaciones = quants.mapped('location_id')
        # Se reporta el anaquel "pendiente" primero: si algo sigue en el anaquel
        # normal, el lote todavia tiene trabajo por hacer.
        if any(u not in (corta | cortesia | retenidos) for u in ubicaciones):
            return 'normal'
        if corta and corta in ubicaciones:
            return 'corta'
        if cortesia and cortesia in ubicaciones:
            return 'cortesia'
        return 'retenido'

    # ------------------------------------------------------------------
    def _amunet_es_producto_terminado(self):
        """Solo el producto terminado se mueve a los anaqueles de promociones."""
        self.ensure_one()
        nombre = self.product_id.categ_id.complete_name or ''
        return nombre == CATEGORIA_PT or nombre.startswith(CATEGORIA_PT + ' /')

    def _amunet_destino_esperado(self):
        """El anaquel donde deberia estar este lote hoy. False si no aplica."""
        self.ensure_one()
        if not self._amunet_es_producto_terminado():
            return False
        corta, cortesia, retenidos = self._amunet_ubicaciones_promocion()
        condicion = self.amunet_condicion_caducidad
        if condicion == 'corta':
            return corta
        if condicion == 'cortesia':
            return cortesia
        if condicion in ('retirar', 'vencido'):
            return retenidos
        # Normal o sin fecha: su lugar es el anaquel de existencias del almacen.
        almacen = self.env['stock.warehouse'].search([('code', '=', 'APT')], limit=1)
        return almacen.lot_stock_id if almacen else False

    def _amunet_quants_movibles(self, destino):
        """Existencias del lote que aun no estan en el anaquel destino."""
        self.ensure_one()
        if not destino:
            return self.env['stock.quant'].browse()
        return self.quant_ids.filtered(
            lambda q: q.location_id.usage == 'internal'
            and q.quantity > 0
            and q.location_id != destino)

    def action_amunet_confirmar_movimiento(self):
        """Abre el asistente para registrar que ya se movieron las cajas."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Confirmar movimiento de anaquel'),
            'res_model': 'amunet.movimiento.caducidad',
            'view_mode': 'form',
            'target': 'new',
            'context': dict(self.env.context, active_ids=self.ids,
                            active_model='stock.lot'),
        }

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

            donde = lote._amunet_donde_esta()
            if lote.amunet_ubicacion_condicion != donde:
                valores['amunet_ubicacion_condicion'] = donde

            # Debe moverse cuando el calendario ya lo cambio de condicion pero
            # la mercancia sigue donde estaba. 'retirar' y 'vencido' tambien
            # piden movimiento: salen de la venta.
            esperado = {
                'corta': 'corta',
                'cortesia': 'cortesia',
                'retirar': 'retenido',
                'vencido': 'retenido',
            }.get(condicion, 'normal')
            if donde == 'sin_stock' or not lote._amunet_es_producto_terminado():
                mover = False
            else:
                mover = (donde != esperado)
            if lote.amunet_requiere_movimiento != mover:
                valores['amunet_requiere_movimiento'] = mover
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
