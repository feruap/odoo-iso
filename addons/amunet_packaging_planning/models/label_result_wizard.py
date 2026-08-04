# -*- coding: utf-8 -*-
from odoo import models, fields


class AmunetPackagingLabelResult(models.TransientModel):
    """Dialogo que lista los archivos de etiquetas generados por el plan
    (caja + buffer) para que el usuario los revise y descargue juntos,
    en la misma lista, desde el boton 'Etiquetas de caja (PPTX)'."""
    _name = 'amunet.packaging.label.result'
    _description = 'Etiquetas generadas del plan de empaque'

    plan_id = fields.Many2one('amunet.packaging.plan', string='Plan')
    orden = fields.Char(string='Orden')
    line_ids = fields.One2many(
        'amunet.packaging.label.result.line', 'result_id',
        string='Archivos generados')
    archivo_todas = fields.Binary(string='Todas juntas (PPTX)')
    archivo_todas_filename = fields.Char(string='Nombre archivo todas')

    def action_descargar_todas(self):
        """Descarga un unico PPTX con TODAS las etiquetas (caja + buffer)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': ('/web/content?model=amunet.packaging.label.result'
                    '&id=%s&field=archivo_todas'
                    '&filename_field=archivo_todas_filename'
                    '&download=true') % self.id,
            'target': 'self',
        }


class AmunetPackagingLabelResultLine(models.TransientModel):
    _name = 'amunet.packaging.label.result.line'
    _description = 'Archivo de etiqueta generado'
    _order = 'sequence, id'

    result_id = fields.Many2one(
        'amunet.packaging.label.result', string='Resultado',
        required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    tipo = fields.Char(string='Tipo')
    name = fields.Char(string='Archivo')
    archivo = fields.Binary(string='Descargar')
    archivo_filename = fields.Char(string='Nombre de archivo')
    preview = fields.Binary(string='Vista previa', attachment=False,
                            help='Imagen de UNA etiqueta para revisarla antes '
                                 'de descargar el archivo completo.')

    def action_descargar(self):
        """Descarga directa del archivo de la fila, sin abrir formulario."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': ('/web/content?model=amunet.packaging.label.result.line'
                    '&id=%s&field=archivo&filename_field=archivo_filename'
                    '&download=true') % self.id,
            'target': 'self',
        }

    def action_ver_preview(self):
        """Abre la vista previa de la etiqueta EN GRANDE, en un dialogo."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.name or 'Vista previa de etiqueta',
            'res_model': 'amunet.packaging.label.result.line',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref(
                'amunet_packaging_planning.view_label_result_line_preview_form').id,
            'target': 'new',
        }
