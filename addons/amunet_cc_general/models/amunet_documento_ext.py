from odoo import api, fields, models


class AmunetDocumentoExt(models.Model):
    _inherit = 'amunet.documento'

    tiene_cc_aprobado = fields.Boolean(
        compute='_compute_tiene_cc_aprobado',
        string='Tiene CC aprobado',
    )

    def _compute_display_name(self):
        for rec in self:
            if rec.codigo and rec.codigo != 'Nuevo':
                rec.display_name = '%s — %s' % (rec.codigo, rec.name or '')
            else:
                rec.display_name = rec.name or rec.codigo or ''

    def action_open_sugerencia_wizard(self):
        """Redirige al nuevo CC General pre-llenado con este documento."""
        self.ensure_one()
        nombre = '%s — %s' % (self.codigo, self.name) if self.codigo and self.codigo != 'Nuevo' else (self.name or '')
        return {
            'name': 'Nuevo Control de Cambios: %s' % self.codigo,
            'type': 'ir.actions.act_window',
            'res_model': 'amunet.cc.general',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_documento_afectado_id': self.id,
                'default_tipo_elemento': 'pno',
                'default_nombre_documento': nombre,
            },
        }

    def _compute_tiene_cc_aprobado(self):
        for rec in self:
            rec.tiene_cc_aprobado = self.env['amunet.cc.general'].search_count([
                ('documento_afectado_id', '=', rec.id),
                ('state', '=', 'aceptado'),
            ]) > 0

    def write(self, vals):
        if vals.get('state') == 'vigente':
            becoming_vigente = self.filtered(lambda d: d.state != 'vigente')
        else:
            becoming_vigente = self.env['amunet.documento']

        res = super().write(vals)

        if becoming_vigente:
            today_str = fields.Date.today().strftime('%d/%m/%Y')
            ccs = self.env['amunet.cc.general'].search([
                ('documento_afectado_id', 'in', becoming_vigente.ids),
                ('state', '=', 'aceptado'),
                ('lote_aplicacion', '=', False),
            ])
            if ccs:
                ccs.write({'lote_aplicacion': today_str})

        return res
