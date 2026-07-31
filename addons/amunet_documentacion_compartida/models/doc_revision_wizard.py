from odoo import models, fields, api
from odoo.exceptions import ValidationError

CAMPOS = {
    'rev_materiales': 'Precauciones',
    'rev_volumenes': 'Volúmenes de reactivos',
    'rev_tiempos': 'Tiempos de interpretación',
    'rev_interpretacion': 'Interpretación',
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

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        doc_id = vals.get('doc_id') or self.env.context.get('default_doc_id')
        campo = vals.get('campo') or self.env.context.get('default_campo')
        if doc_id and campo:
            ultimo = self.env['amunet.doc.revision.historial'].search([
                ('doc_id', '=', doc_id),
                ('campo', '=', campo),
                ('motivo', '!=', False),
            ], order='fecha desc', limit=1)
            if ultimo:
                vals['observacion'] = ultimo.motivo
        return vals

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
        # sudo() necesario: el analista tiene perm_write=0 en el modelo principal;
        # la validación de negocio ya ocurrió en el override write() con el uid real.
        self.doc_id.sudo().write(vals)
        return {'type': 'ir.actions.act_window_close'}
