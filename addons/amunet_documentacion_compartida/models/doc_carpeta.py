from odoo import models, fields, api


class DocCarpeta(models.Model):
    _name = 'amunet.doc.carpeta'
    _description = 'Carpeta de Documentación'
    _order = 'sequence, name'

    name = fields.Char(string='Nombre', required=True)
    sequence = fields.Integer(default=10)
    parent_id = fields.Many2one('amunet.doc.carpeta', string='Carpeta padre', ondelete='restrict')
    child_ids = fields.One2many('amunet.doc.carpeta', 'parent_id', string='Sub-carpetas')
    doc_ids = fields.One2many('amunet.doc.compartida', 'carpeta_id', string='Documentos')

    child_count = fields.Integer(compute='_compute_counts')
    doc_count = fields.Integer(compute='_compute_counts')

    @api.depends('child_ids', 'doc_ids')
    def _compute_counts(self):
        for rec in self:
            rec.child_count = len(rec.child_ids)
            rec.doc_count = len(rec.doc_ids)

    def action_open(self):
        """Navega dentro de la carpeta: muestra sub-carpetas o documentos."""
        self.ensure_one()
        if self.child_ids:
            return {
                'type': 'ir.actions.act_window',
                'name': self.name,
                'res_model': 'amunet.doc.carpeta',
                'view_mode': 'kanban,list',
                'domain': [('parent_id', '=', self.id)],
                'context': {'default_parent_id': self.id,
                            'carpeta_breadcrumb': self.name},
            }
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': 'amunet.doc.compartida',
            'view_mode': 'list,form',
            'domain': [('carpeta_id', '=', self.id)],
            'context': {
                'default_carpeta_id': self.id,
                'hide_equipos_cols': self.name == 'EQUIPOS',
            },
        }
