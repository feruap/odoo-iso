from odoo import models, fields
from odoo.exceptions import UserError


class DocTomarWizard(models.TransientModel):
    _name = 'amunet.doc.tomar.wizard'
    _description = 'Confirmar tomar revisión activa'

    doc_id = fields.Many2one('amunet.doc.compartida', required=True)
    doc_name = fields.Char(related='doc_id.name', readonly=True)
    revisor_actual_id = fields.Many2one(
        related='doc_id.revisor_activo_id', readonly=True, string='Revisor actual')

    def action_confirmar(self):
        doc = self.doc_id
        if doc.state == 'aprobado':
            raise UserError('Este manual ya fue aprobado.')
        anterior = doc.revisor_activo_id
        doc.revisor_activo_id = self.env.user.id
        doc.message_post(
            body=f'🔄 {self.env.user.name} tomó la revisión activa '
                 f'(antes: {anterior.name}).',
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )
        return {'type': 'ir.actions.act_window_close'}
