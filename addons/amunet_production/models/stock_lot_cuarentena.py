# -*- coding: utf-8 -*-
"""Cuarentena de ingreso: el reloj que retrasa el analisis.

EL PROBLEMA QUE RESUELVE. Un vial recien llenado no se puede juzgar el mismo
dia: hay que dejarlo reposar para que se manifieste lo que traiga. Mery lo
pidio el 30-sep-2026 para el Llenado de Viales, y lo pidio asi: que el analisis
NO SE GENERE hasta pasados los dias, no que se genere y se quede detenido. Un
analisis que existe es un pendiente de Calidad; si nace el dia 1 y no se puede
tocar hasta el dia 5, ensucia la bandeja cuatro dias.

COMO FUNCIONA.
  1. Almacen valida la entrada y el material cae en Control de calidad.
     Ahi se sella el inicio y el fin (inicio + dias del producto).
  2. Un cron diario recorre los lotes cuyo fin ya paso y les genera el
     analisis con el punto de control del producto.
  3. El lote no sale de Control de calidad antes de tiempo: el candado vive
     en stock_picking.py.

El reloj arranca cuando el material esta FISICAMENTE en cuarentena, no cuando
se fabrico. Producir un lunes y entregarlo el viernes no adelanta el reposo.

ALCANCE. Solo toca productos con 'amunet_dias_cuarentena' > 0. Con el default
en cero -- que es todo el catalogo menos los 12 viales -- el analisis se sigue
generando al validar la entrada, exactamente como hoy.
"""
import logging

from markupsafe import Markup

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class StockLot(models.Model):
    _inherit = 'stock.lot'

    amunet_cuarentena_inicio = fields.Datetime(
        string='Entró a cuarentena',
        readonly=True, copy=False,
        help='Momento en que Almacén validó la entrada y el material quedó en '
             'Control de calidad. Aquí arranca el reposo.')
    amunet_cuarentena_fin = fields.Datetime(
        string='Cuarentena cumplida el',
        readonly=True, copy=False,
        help='Fecha a partir de la cual se genera el análisis de este lote.')
    amunet_cuarentena_estado = fields.Selection(
        [('ninguna', 'Sin cuarentena'),
         ('en_curso', 'En cuarentena'),
         ('cumplida', 'Cuarentena cumplida')],
        string='Estado de cuarentena',
        compute='_compute_amunet_cuarentena_estado')

    @api.depends('amunet_cuarentena_inicio', 'amunet_cuarentena_fin')
    def _compute_amunet_cuarentena_estado(self):
        ahora = fields.Datetime.now()
        for lote in self:
            if not lote.amunet_cuarentena_fin:
                lote.amunet_cuarentena_estado = 'ninguna'
            elif lote.amunet_cuarentena_fin > ahora:
                lote.amunet_cuarentena_estado = 'en_curso'
            else:
                lote.amunet_cuarentena_estado = 'cumplida'

    def _amunet_iniciar_cuarentena(self, picking=False):
        """Sella el reloj. Idempotente: si ya estaba sellado no lo reinicia.

        Que no reinicie importa: un lote puede pasar por varios movimientos
        dentro de Control de calidad -- un reacomodo, una correccion -- y cada
        uno volveria a poner el contador en cero. El reposo se cuenta desde la
        PRIMERA vez que el material piso la cuarentena.
        """
        from datetime import timedelta
        for lote in self:
            if lote.amunet_cuarentena_inicio:
                continue
            dias = lote.product_id.product_tmpl_id.amunet_dias_cuarentena or 0
            if dias <= 0:
                continue
            inicio = fields.Datetime.now()
            lote.sudo().write({
                'amunet_cuarentena_inicio': inicio,
                'amunet_cuarentena_fin': inicio + timedelta(days=dias),
            })
            lote.sudo().message_post(body=Markup(_(
                'Entró a <b>cuarentena de ingreso</b>: %(dias)s días. '
                'Su análisis se genera solo a partir del '
                '<b>%(fin)s</b>.%(doc)s',
                dias=dias,
                fin=(inicio + timedelta(days=dias)).strftime('%d/%m/%Y'),
                doc=(' (entrada %s)' % picking.name) if picking else '',
            )))

    @api.model
    def _cron_amunet_analisis_post_cuarentena(self):
        """Genera el analisis de los lotes que ya cumplieron su reposo.

        Corre diario. Busca lotes con la cuarentena vencida que todavia no
        tengan analisis y se los crea, con los parametros del punto de control
        del producto -- la misma fuente que usa una recepcion de proveedor.

        Si el producto no esta en ningun punto, el analisis se genera IGUAL y
        sin parametros: esa es la regla que fijo Mery el 28-sep-2026 cuando
        aparecieron 7 lotes parados en cuarentena sin nada que los sacara. Un
        analisis vacio es un pendiente visible; ningun analisis es material
        perdido.
        """
        Check = self.env['amunet.quality.check'].sudo()
        ahora = fields.Datetime.now()
        lotes = self.sudo().search([
            ('amunet_cuarentena_fin', '!=', False),
            ('amunet_cuarentena_fin', '<=', ahora),
        ])
        creados = 0
        for lote in lotes:
            if Check.search_count([('lot_id', '=', lote.id)]):
                continue
            # Solo si sigue habiendo material en cuarentena. Un lote que ya
            # salio -- porque se cancelo la entrada, o se devolvio -- no tiene
            # nada que analizar.
            quants = self.env['stock.quant'].sudo().search([
                ('lot_id', '=', lote.id), ('quantity', '>', 0),
                ('location_id.usage', '=', 'internal'),
            ])
            if not any('Control de calidad' in (q.location_id.complete_name or '')
                       for q in quants):
                continue
            try:
                lote._amunet_crear_analisis_de_cuarentena()
                creados += 1
            except Exception:  # noqa: BLE001
                _logger.exception(
                    'No se pudo generar el analisis de cuarentena del lote %s',
                    lote.name)
        if creados:
            _logger.info('Cuarentena: %s analisis generados.', creados)
        return creados

    def _amunet_crear_analisis_de_cuarentena(self):
        """Crea el analisis de un lote que cumplio cuarentena."""
        self.ensure_one()
        producto = self.product_id
        Check = self.env['amunet.quality.check'].sudo()
        vals = {
            'product_id': producto.id,
            'lot_id': self.id,
            'lot_amunet': self.name,
        }
        if producto.uom_id:
            vals['sampling_uom_id'] = producto.uom_id.id
        if self.expiration_date:
            vals['expiration_date'] = self.expiration_date
        if 'manufacturing_date' in self._fields and self.manufacturing_date:
            vals['manufacturing_date'] = self.manufacturing_date
        qc = Check.create(vals)

        puntos = self.env['amunet.quality.point'].sudo().search([
            ('active', '=', True),
            ('product_ids', 'in', producto.id),
        ])
        for punto in puntos:
            for param in punto.parameter_ids:
                if qc.test_line_ids.filtered(lambda l: l.parameter_id == param):
                    continue
                self.env['amunet.quality.test.line'].sudo().create({
                    'check_id': qc.id,
                    'parameter_id': param.id,
                })
        if not qc.test_line_ids:
            # Sin punto de control, los parametros se toman del producto, que
            # es de donde los lee tambien el analisis de produccion.
            try:
                qc._load_product_parameters()
            except Exception:  # noqa: BLE001
                _logger.exception(
                    'No se pudieron cargar los parametros del producto %s',
                    producto.default_code)
        qc.message_post(body=Markup(_(
            'Análisis generado al cumplirse la <b>cuarentena de ingreso</b> '
            'del lote %(lote)s (entró el %(ini)s, cumplió el %(fin)s).',
            lote=self.name or '',
            ini=self.amunet_cuarentena_inicio.strftime('%d/%m/%Y'),
            fin=self.amunet_cuarentena_fin.strftime('%d/%m/%Y'),
        )))
        self.sudo().message_post(body=Markup(_(
            'Cuarentena cumplida. Se generó el análisis <b>%s</b>.')) % qc.name)
        return qc
