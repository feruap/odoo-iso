# -*- coding: utf-8 -*-
from odoo import fields, models
from . import amunet_documento as _doc_module


class AmunetDocumentoFormato(models.Model):
    _name = 'amunet.documento.formato'
    _description = 'Formato derivado descargable'
    _order = 'sequence, id'

    documento_id = fields.Many2one(
        'amunet.documento', string='Documento', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    codigo = fields.Char(string='Código', required=True)
    nombre = fields.Char(string='Nombre del formato', required=True)
    archivo = fields.Binary(string='Archivo', attachment=True)
    archivo_filename = fields.Char(string='Nombre de archivo')
    doc_area = fields.Selection(
        related='documento_id.area', string='Área', store=True)
    doc_codigo = fields.Char(
        related='documento_id.codigo', string='Código PNO', store=False)

    def _check_editable(self, vals=None):
        _doc_module._check_documento_child_editable(self, vals)

    def write(self, vals):
        self._check_editable(vals)
        return super().write(vals)

    def unlink(self):
        self._check_editable()
        return super().unlink()
