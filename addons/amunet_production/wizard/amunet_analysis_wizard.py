# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AmunetAnalysisWizard(models.TransientModel):
    _name = 'amunet.production.analysis.wizard'
    _description = 'Wizard de Solicitud de Análisis de Producción'

    production_id = fields.Many2one('mrp.production', string='Orden de Producción', required=True)
    product_id = fields.Many2one(related='production_id.product_id', string='Producto a Analizar', readonly=True)
    product_qty = fields.Float(related='production_id.product_qty', string='Cantidad Planeada', readonly=True)
    amunet_expiration_text = fields.Char(related='production_id.amunet_expiration_text', string='Caducidad Declarada', readonly=True)
    lote_producido = fields.Char(string='Lote', compute='_compute_lote_producido', readonly=True)

    @api.depends('production_id')
    def _compute_lote_producido(self):
        for w in self:
            lots = w.production_id.lot_producing_ids
            w.lote_producido = ', '.join(lots.mapped('name')) if lots else (w.production_id.solution_lot_id or '')

    # ------------------------------------------------------------------
    # ALCANCE DEL ANALISIS
    #
    # La cantidad con la que se ABRE una orden es TEORICA: es lo que se
    # planeo, no lo que salio. Cuando se manda a analizar una PARTE del lote
    # todavia NO se sabe el total, asi que pedirlo ahi obliga a inventar un
    # numero — y ese numero es el que despues determina cuanto entra al
    # inventario al cerrar. De ahi salen las piezas fantasma.
    #
    #   PARCIAL   solo pregunta cuantas piezas se mandan a analizar AHORA.
    #             El total declarado de la orden se va ACUMULANDO con cada
    #             parcial, de modo que el ULTIMO parcial queda como el total
    #             del lote (decision de Mery, 07-sep-2026).
    #   COMPLETO  pregunta el total fabricado, que en ese momento SI se
    #             conoce, y cubre todo lo que faltara por analizar.
    # ------------------------------------------------------------------
    tipo_analisis = fields.Selection([
        ('completo', 'Completo — ya se conoce el total fabricado'),
        ('parcial', 'Parcial — se manda a analizar una parte del lote'),
    ], string='Alcance del análisis', default='completo', required=True)

    qty_analizada = fields.Float(
        string='Piezas que se mandan a analizar',
        help='Cuántas piezas del lote se envían a Calidad en ESTA solicitud. '
             'Es lo único que se sabe con certeza al pedir un análisis parcial.')

    qty_fabricada = fields.Float(
        string='Total de piezas fabricadas',
        help='Total real que salió del lote. Solo se pide en el análisis '
             'completo, que es cuando ya se conoce.')

    qty_ya_analizada = fields.Float(
        string='Ya enviadas en análisis previos', readonly=True)

    qty_acumulada = fields.Float(
        string='Quedarían enviadas en total', compute='_compute_qty_acumulada', readonly=True)

    @api.depends('qty_analizada', 'qty_ya_analizada')
    def _compute_qty_acumulada(self):
        for w in self:
            w.qty_acumulada = (w.qty_ya_analizada or 0.0) + (w.qty_analizada or 0.0)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        prod_id = res.get('production_id') or self.env.context.get('default_production_id')
        if prod_id:
            prod = self.env['mrp.production'].browse(prod_id)
            ya = sum(prod.amunet_qc_check_ids.mapped('amunet_qty_analizada'))
            res['qty_ya_analizada'] = ya
            # Sugerencia para el completo: lo que la orden traiga registrado o
            # lo planeado. El usuario lo corrige con el dato real.
            base = prod.qty_producing or prod.product_qty or 0.0
            res.setdefault('qty_fabricada', base)
            res.setdefault('qty_analizada', max(0.0, base - ya))
        return res

    def action_confirm_analysis(self):
        """Crea el análisis de Calidad y registra el alcance."""
        self.ensure_one()
        prod = self.production_id
        ya = self.qty_ya_analizada or 0.0

        if self.tipo_analisis == 'completo':
            if (self.qty_fabricada or 0.0) <= 0:
                raise UserError(_(
                    'Indica el total de piezas fabricadas del lote (mayor a 0).'))
            if self.qty_fabricada < ya:
                raise UserError(_(
                    'El total que declaras (%(fab)s) es menor que las %(ya)s '
                    'pieza(s) que ya se enviaron a analizar en solicitudes '
                    'previas.') % {'fab': self.qty_fabricada, 'ya': ya})
            cubre = self.qty_fabricada - ya
            total_declarado = self.qty_fabricada
        else:
            if (self.qty_analizada or 0.0) <= 0:
                raise UserError(_(
                    'Indica cuántas piezas mandas a analizar en esta solicitud '
                    '(mayor a 0).'))
            cubre = self.qty_analizada
            # El total va creciendo con cada parcial: el ultimo queda como total.
            total_declarado = ya + cubre

        if prod.state == 'draft':
            prod.action_confirm()
        if prod.state == 'confirmed':
            prod.action_start()

        prod.qty_producing = total_declarado
        prod.write({
            'quality_analysis_status': 'requested',
            'amunet_pt_qty_solicitada': total_declarado,
        })

        qc = self._amunet_crear_analisis_calidad(cubre)

        if self.tipo_analisis == 'parcial':
            cuerpo = _(
                'Análisis <b>PARCIAL</b>: se mandan <b>%(cubre)s</b> pieza(s) a '
                'Calidad (análisis <b>%(qc)s</b>). Acumulado del lote: '
                '<b>%(total)s</b> pieza(s). Si este fue el último parcial, ese '
                'es el total del lote.'
            ) % {'cubre': cubre, 'qc': qc.name, 'total': total_declarado}
        else:
            cuerpo = _(
                'Análisis <b>COMPLETO</b>: el lote fabricó <b>%(total)s</b> '
                'pieza(s); este análisis cubre las <b>%(cubre)s</b> que faltaban. '
                'Se generó <b>%(qc)s</b>.'
            ) % {'total': total_declarado, 'cubre': cubre, 'qc': qc.name}
        prod.message_post(body=cuerpo)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'amunet.quality.check',
            'res_id': qc.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _amunet_crear_analisis_calidad(self, cubre):
        """Crea el análisis del módulo de Calidad con los parámetros del producto.

        Se usa `_load_product_parameters()` y no `apply_quality_points()`: los
        puntos de control cuelgan de un tipo de operación (una recepción) y aquí
        no hay picking — el análisis es del producto que se fabricó.
        """
        self.ensure_one()
        prod = self.production_id
        producto = prod.product_id

        if not producto.product_tmpl_id.qc_parameter_rel_ids:
            raise UserError(_(
                'El producto %(prod)s no tiene parámetros de calidad '
                'configurados, así que el análisis nacería vacío.\n\n'
                'Pídele a Calidad que los configure antes de solicitar el '
                'análisis de esta orden.'
            ) % {'prod': producto.display_name})

        QC = self.env['amunet.quality.check']
        vals = {
            'product_id': producto.id,
            'amunet_production_id': prod.id,
            'analysis_type': 'initial',
            'state': 'draft',
            'amunet_qty_analizada': cubre,
            'amunet_analisis_parcial': self.tipo_analisis == 'parcial',
        }
        lote = prod.lot_producing_ids[:1]
        if lote:
            vals['lot_id'] = lote.id
        if 'quantity' in QC._fields:
            vals['quantity'] = cubre
        if 'expiration_date' in QC._fields and hasattr(prod, '_amunet_caducidad_de_la_orden'):
            fecha = prod._amunet_caducidad_de_la_orden()
            if fecha:
                vals['expiration_date'] = fecha

        qc = QC.create(vals)
        qc._load_product_parameters()
        return qc
