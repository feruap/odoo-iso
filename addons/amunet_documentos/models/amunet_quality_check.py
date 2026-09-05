# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AmunetQualityCheck(models.Model):
    """Liga el analisis con la ficha de prueba rapida del catalogo.

    El campo vive aqui y no en amunet_quality porque el modelo
    amunet.prueba.rapida se define en este modulo, que ya depende
    de amunet_quality. Declararlo al reves genera dependencia circular.
    """
    _inherit = 'amunet.quality.check'

    prueba_rapida_id = fields.Many2one(
        'amunet.prueba.rapida',
        string='Ficha de prueba rápida',
        compute='_compute_prueba_rapida_id',
        store=False,
    )

    @api.depends('product_id')
    def _compute_prueba_rapida_id(self):
        PruebaRapida = self.env['amunet.prueba.rapida']
        for rec in self:
            code = rec.product_id.default_code or ''
            rec.prueba_rapida_id = PruebaRapida.search(
                [('referencia', '=', code)], limit=1
            ) if code else PruebaRapida
