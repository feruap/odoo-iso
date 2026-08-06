from odoo import api, fields, models


class AmunetDocumentoExt(models.Model):
    _inherit = 'amunet.documento'

    def _compute_display_name(self):
        for rec in self:
            if rec.codigo and rec.codigo != 'Nuevo':
                rec.display_name = '%s — %s' % (rec.codigo, rec.name or '')
            else:
                rec.display_name = rec.name or rec.codigo or ''

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
