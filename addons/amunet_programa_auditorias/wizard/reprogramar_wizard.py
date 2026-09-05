from odoo import fields, models, _
from odoo.exceptions import ValidationError


class AmunetProgramaReprogramarWizard(models.TransientModel):
    _name = 'amunet.programa.reprogramar.wizard'
    _description = 'Reprogramar programa anual de auditorías'

    programa_id = fields.Many2one(
        'amunet.programa.auditoria', required=True, readonly=True)
    motivo = fields.Text(
        string='Motivo de reprogramación', required=True,
        placeholder='Describe brevemente por qué se necesita reprogramar...')

    def action_confirmar(self):
        self.ensure_one()
        if not self.motivo or not self.motivo.strip():
            raise ValidationError(_('El motivo es obligatorio.'))
        prog = self.programa_id
        prog.write({
            'state': 'borrador',
            'autorizo_id': False,
            'fecha_autorizacion': False,
        })
        prog.message_post(
            body=_('Programa regresado a borrador para reprogramación.<br/><b>Motivo:</b> %s')
                 % self.motivo.strip(),
            subtype_xmlid='mail.mt_note',
        )
        return {'type': 'ir.actions.act_window_close'}
