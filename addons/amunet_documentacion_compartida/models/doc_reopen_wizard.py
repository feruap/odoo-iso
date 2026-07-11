from odoo import models, fields


class DocReopenWizard(models.TransientModel):
    _name = 'amunet.doc.reopen.wizard'
    _description = 'Confirmar reapertura de revisión'

    doc_id = fields.Many2one('amunet.doc.compartida', required=True)
    doc_name = fields.Char(related='doc_id.name', readonly=True)
    cerrado_por_id = fields.Many2one(
        related='doc_id.revisado_por_id', readonly=True, string='Cerrado por')
    cerrado_en = fields.Datetime(
        related='doc_id.fecha_revision', readonly=True, string='Fecha de cierre')

    def action_confirmar(self):
        doc = self.doc_id
        uid = self.env.user.id
        # Registrar reapertura en el historial
        self.env['amunet.doc.revision.historial'].sudo().create({
            'doc_id': doc.id,
            'usuario_id': uid,
            'accion': 'reapertura',
        })
        # Limpiar revisión anterior, INVALIDAR la firma y regresar a PENDIENTE,
        # asignando el cerrojo al que reabre.
        doc.with_context(bypass_revisor_check=True).write({
            'rev_materiales': False,
            'rev_volumenes': False,
            'rev_tiempos': False,
            'rev_adicional': False,
            'observaciones': False,
            'revisado_por_id': False,
            'fecha_revision': False,
            'revisor_activo_id': uid,
            'state': 'pendiente',
            'firmante_id': False,
            'fecha_firma': False,
        })
        grupo = self.env.ref(
            'amunet_documentacion_compartida.group_doc_compartida_user',
            raise_if_not_found=False)
        partner_ids = grupo.user_ids.mapped('partner_id').ids if grupo else []
        doc.message_post(
            body=f'🔄 <b>{self.env.user.name}</b> reabrió la revisión de este manual '
                 f'para corrección. El estatus vuelve a PENDIENTE.',
            partner_ids=partner_ids,
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
        )
        return {'type': 'ir.actions.act_window_close'}
