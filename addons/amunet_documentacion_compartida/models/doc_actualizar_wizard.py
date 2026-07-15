from odoo import models, fields

DIANA_UID = 64
_UIDS_VISORES = [69, 61]  # Stacy, Mery


class DocActualizarWizard(models.TransientModel):
    _name = 'amunet.doc.actualizar.wizard'
    _description = 'Confirmar manual aprobado disponible'

    doc_id = fields.Many2one('amunet.doc.compartida', required=True, readonly=True)
    doc_name = fields.Char(related='doc_id.name', readonly=True)

    def action_aceptar(self):
        doc = self.doc_id
        doc.sudo().write({'pdf_disponible': True})
        doc.message_post(
            body=f'✅ Manual <b>{doc.name}</b> confirmado como disponible. '
                 f'El PDF puede descargarse directamente desde este módulo.',
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )
        # Cerrar actividad pendiente de Diana
        doc.activity_ids.filtered(
            lambda a: a.user_id.id == DIANA_UID
            and 'aprobado' in (a.summary or '').lower()
        ).action_done()
        # Notificar a Stacy y Mery que el PDF ya está disponible
        tipo = self.env.ref('mail.mail_activity_data_todo')
        visores = self.env['res.users'].sudo().browse(_UIDS_VISORES).filtered('active')
        for user in visores:
            doc.activity_schedule(
                activity_type_id=tipo.id,
                summary=f'Manual disponible: {doc.name}',
                note=f'El manual <b>{doc.name}</b> ha sido aprobado y ya puedes descargarlo desde el módulo.',
                user_id=user.id,
            )
        return {'type': 'ir.actions.act_window_close'}

    def action_posponer(self):
        return {'type': 'ir.actions.act_window_close'}
