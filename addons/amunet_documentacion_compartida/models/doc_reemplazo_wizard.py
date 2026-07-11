from odoo import models, fields, api
from odoo.exceptions import ValidationError


class DocReemplazoWizard(models.TransientModel):
    _name = 'amunet.doc.reemplazo.wizard'
    _description = 'Reemplazar PDF del manual'

    doc_id = fields.Many2one('amunet.doc.compartida', required=True)
    doc_name = fields.Char(related='doc_id.name', readonly=True)
    nuevo_archivo = fields.Binary(string='Nuevo PDF', required=True)
    nuevo_filename = fields.Char(string='Nombre del archivo')

    @api.constrains('nuevo_filename')
    def _check_pdf(self):
        for rec in self:
            if rec.nuevo_filename and not rec.nuevo_filename.lower().endswith('.pdf'):
                raise ValidationError(
                    f'Solo se aceptan archivos PDF. '
                    f'El archivo "{rec.nuevo_filename}" no es válido.')

    def action_confirmar(self):
        doc = self.doc_id
        # Solo reemplazar el archivo; la revisión anterior se conserva
        doc.with_context(bypass_revisor_check=True).write({
            'manual_file': self.nuevo_archivo,
            'manual_filename': self.nuevo_filename,
        })
        doc._notificar_recarga_pdf()
        return {'type': 'ir.actions.act_window_close'}
