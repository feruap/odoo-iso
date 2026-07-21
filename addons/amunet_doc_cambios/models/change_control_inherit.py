from odoo import models

JORGE_UID = 70

_QUALITY_GROUPS = [
    'amunet_quality.group_quality_user',
    'amunet_quality.group_quality_supervisor',
    'amunet_quality.group_quality_manager',
]


class AmunetChangeControlDoc(models.Model):
    _inherit = 'amunet.change.control'

    def _signature_quality_approve(self):
        res = super()._signature_quality_approve()
        for rec in self:
            if rec.request_type == 'lot_instruction_change' and rec.sudo().production_id:
                prod_name = rec.sudo().production_id.name
                tipo = self.env.ref('mail.mail_activity_data_todo')
                nota = (
                    f'<p>Calidad aprobó el cambio reportado en la orden '
                    f'<b>{prod_name}</b>.</p>'
                    f'<p><b>Descripción:</b> {rec.rationale}</p>'
                    f'<p>Verifica si el instructivo de uso requiere actualización.</p>'
                )
                # Reúne destinatarios: Jorge + todos los usuarios de Calidad
                destinatarios = self.env['res.users'].sudo().browse(JORGE_UID)
                for xmlid in _QUALITY_GROUPS:
                    group = self.env.ref(xmlid, raise_if_not_found=False)
                    if group:
                        destinatarios |= group.sudo().users
                for user in destinatarios.filtered('active'):
                    if user.id != self.env.user.id:
                        rec.activity_schedule(
                            activity_type_id=tipo.id,
                            summary=f'Revisar instructivo — cambio aprobado en {prod_name}',
                            note=nota,
                            user_id=user.id,
                        )
        return res
