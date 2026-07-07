from odoo import models, fields, api


class DocCompartida(models.Model):
    _name = 'amunet.doc.compartida'
    _description = 'Documentación Compartida'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ── Columna 1: Manual ────────────────────────────────────
    name = fields.Char(string='Manual', required=True, tracking=True)
    carpeta_id = fields.Many2one('amunet.doc.carpeta', string='Carpeta', tracking=True)
    manual_file = fields.Binary(string='Archivo DOCX', attachment=True)
    manual_filename = fields.Char(string='Nombre del archivo')

    # ── Columna 2: Revisión Calidad (3 criterios) ────────────
    rev_materiales = fields.Selection(
        [('ok', '✓'), ('fail', '✗')],
        string='Materiales', tracking=True)
    rev_volumenes = fields.Selection(
        [('ok', '✓'), ('fail', '✗')],
        string='Volúmenes de reactivos', tracking=True)
    rev_tiempos = fields.Selection(
        [('ok', '✓'), ('fail', '✗')],
        string='Tiempos de interpretación', tracking=True)

    # ── Columna 3: Observaciones ─────────────────────────────
    obs_requeridas = fields.Boolean(compute='_compute_estado', store=True)
    observaciones = fields.Text(string='Observaciones', tracking=True)

    # ── Columna 4: Estatus ────────────────────────────────────
    state = fields.Selection(
        [('aprobado', 'APROBADO'), ('pendiente', 'PENDIENTE')],
        string='Estatus', default='pendiente',
        compute='_compute_estado', store=True, tracking=True)

    @api.depends('rev_materiales', 'rev_volumenes', 'rev_tiempos')
    def _compute_estado(self):
        for rec in self:
            reviews = [rec.rev_materiales, rec.rev_volumenes, rec.rev_tiempos]
            all_ok = all(r == 'ok' for r in reviews)
            any_fail = any(r == 'fail' for r in reviews)

            rec.state = 'aprobado' if all_ok else 'pendiente'
            rec.obs_requeridas = any_fail
            # Si todas están aprobadas, limpia observaciones y pone "Ninguna"
            if all_ok and not rec.observaciones:
                rec.observaciones = 'Ninguna'
