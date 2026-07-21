from odoo import models, fields

DIANA_UID = 64


class ReporteCambioWizard(models.TransientModel):
    _name = 'amunet.reporte.cambio.wizard'
    _description = 'Reportar cambio o novedad en producción'

    production_id = fields.Many2one('mrp.production', required=True, readonly=True)
    descripcion = fields.Text(
        string='¿Qué notaste diferente?',
        required=True,
        help='Describe brevemente el cambio o novedad que detectaste.',
    )
    instruccion_vigente = fields.Text(
        string='¿Qué dice el proceso original?',
        help='Opcional. Ej: 2 gotas de buffer según el instructivo.',
    )
    instruccion_propuesta = fields.Text(
        string='¿Qué se hizo en cambio?',
        help='Opcional. Ej: se usaron 3 gotas de buffer.',
    )

    def action_enviar(self):
        self.ensure_one()
        prod = self.sudo().production_id
        lot = prod.lot_producing_ids[:1]
        cc = self.env['amunet.change.control'].sudo().create({
            'title': f'Cambio reportado — {prod.name}',
            'request_type': 'lot_instruction_change',
            'scope': 'lot',
            'product_id': prod.product_id.id,
            'lot_id': lot.id if lot else False,
            'production_id': prod.id,
            'rationale': f'<p>{self.descripcion}</p>',
            'current_instruction': self.instruccion_vigente or '',
            'proposed_instruction': self.instruccion_propuesta or '',
            'risk_level': 'medium',
            'regulatory_impact': 'iso_13485',
            'requested_by_id': self.env.user.id,
        })
        tipo = self.env.ref('mail.mail_activity_data_todo')
        cc.activity_schedule(
            activity_type_id=tipo.id,
            summary=f'Cambio reportado en {prod.name} — revisar si impacta el instructivo',
            note=(
                f'<p><b>{self.env.user.name}</b> reportó un cambio en la orden '
                f'<b>{prod.name}</b>:</p>'
                f'<p>{self.descripcion}</p>'
                f'<p>Revisa el registro, completa la evaluación y aprueba o rechaza.</p>'
            ),
            user_id=DIANA_UID,
        )
        cc.message_post(
            body=f'<p>Reporte creado por <b>{self.env.user.name}</b>: {self.descripcion}</p>',
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Reporte enviado',
                'message': 'Calidad recibió tu reporte y lo revisará.',
                'type': 'success',
                'sticky': False,
            },
        }
