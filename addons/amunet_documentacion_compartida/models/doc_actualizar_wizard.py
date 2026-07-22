from odoo import models, fields

# Personas para notificaciones/actividades, por LOGIN (robusto entre bases;
# los UIDs hardcodeados se rompen si se recrea el usuario y no coinciden entre
# staging y produccion).
_LOGIN_DIANA = 's.controldecalidad@amunet.com.mx'      # Diana (Control de Calidad)
_LOGINS_VISORES = [
    'documentacion@amunet.com.mx',                     # Stacy
    'desarrollo@amunet.com.mx',                        # Mery
]


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
        Users = self.env['res.users'].sudo()
        # Cerrar actividad pendiente de Diana (por login, no UID)
        diana = Users.search([('login', '=', _LOGIN_DIANA)], limit=1)
        if diana:
            doc.activity_ids.filtered(
                lambda a: a.user_id == diana
                and 'aprobado' in (a.summary or '').lower()
            ).action_done()
        # Notificar a los visores (Stacy y Mery) que el PDF ya está disponible
        tipo = self.env.ref('mail.mail_activity_data_todo')
        visores = Users.search([('login', 'in', _LOGINS_VISORES), ('active', '=', True)])
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
