# -*- coding: utf-8 -*-
from odoo import models, fields


class AmunetQualityAnexoLine(models.Model):
    _name = 'amunet.quality.anexo.line'
    _description = 'Línea de Anexo General'
    _order = 'sequence, id'

    check_id = fields.Many2one(
        'amunet.quality.check',
        string='Control de Calidad',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(default=10)
    muestra  = fields.Char(string='# Muestra')
    col1     = fields.Char(string='Col 1')
    col2     = fields.Char(string='Col 2')
    col3     = fields.Char(string='Col 3')
    col4     = fields.Char(string='Col 4')
    col5     = fields.Char(string='Col 5')
    col6     = fields.Char(string='Col 6')
