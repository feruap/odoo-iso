from odoo import models, fields, api
from odoo.exceptions import ValidationError

CAMPOS = {
    'rev_materiales': 'Precauciones',
    'rev_volumenes': 'Volúmenes de reactivos',
    'rev_tiempos': 'Tiempos de interpretación',
    'rev_adicional': 'Adicional',
}


class DocRevisionWizard(models.TransientModel):
    _name = 'amunet.doc.revision.wizard'
    _description = 'Marcar resultado de revisión'

    doc_id = fields.Many2one('amunet.doc.compartida', required=True)
    campo = fields.Char(required=True)

    campo_label = fields.Char(compute='_compute_campo_label')
    valor_actual = fields.Selection(
        [('ok', '✓ Correcto'), ('fail', '✗ Incorrecto')],
        string='Resultado actual', readonly=True)
    nuevo_valor = fields.Selection(
        [('ok', '✓ Correcto'), ('fail', '✗ Incorrecto')],
        string='Resultado', required=True)
    observacion = fields.Text(string='Motivo')

    @api.depends('campo')
    def _compute_campo_label(self):
        for rec in self:
            rec.campo_label = CAMPOS.get(rec.campo, rec.campo)

    @api.constrains('nuevo_valor', 'observacion')
    def _check_motivo_requerido(self):
        for rec in self:
            if rec.nuevo_valor == 'fail' and not (rec.observacion or '').strip():
                raise ValidationError(
                    'El motivo es obligatorio cuando se marca ✗ Incorrecto.')

    def action_confirmar(self):
        vals = {self.campo: self.nuevo_valor}
        if self.nuevo_valor == 'fail':
            vals['observaciones'] = self.observacion
        self.doc_id.write(vals)
        return {'type': 'ir.actions.act_window_close'}
