from odoo import models, fields


class DocCambioWizard(models.TransientModel):
    _name = 'amunet.doc.cambio.wizard'
    _description = 'Cambiar resultado de revisión'

    doc_id = fields.Many2one('amunet.doc.compartida', required=True)
    campo = fields.Char(required=True)
    campo_label = fields.Char(string='Criterio')
    valor_actual = fields.Selection(
        [('ok', '✓ Correcto'), ('fail', '✗ Incorrecto')],
        string='Resultado actual', readonly=True)
    nuevo_valor = fields.Selection(
        [('ok', '✓ Correcto'), ('fail', '✗ Incorrecto')],
        string='Nuevo resultado', required=True)

    def action_confirmar(self):
        self.doc_id.write({self.campo: self.nuevo_valor})
        return {'type': 'ir.actions.act_window_close'}
