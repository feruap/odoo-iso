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
        [('ok', '✓ Correcto'), ('fail', '✗ Incorrecto')],
        string='Materiales', tracking=True)
    rev_volumenes = fields.Selection(
        [('ok', '✓ Correcto'), ('fail', '✗ Incorrecto')],
        string='Volúmenes de reactivos', tracking=True)
    rev_tiempos = fields.Selection(
        [('ok', '✓ Correcto'), ('fail', '✗ Incorrecto')],
        string='Tiempos de interpretación', tracking=True)

    # ── Columna 3: Observaciones ─────────────────────────────
    obs_requeridas = fields.Boolean(compute='_compute_estado', store=True)
    observaciones = fields.Text(string='Observaciones', tracking=True)

    # ── Columna 4: Estatus ────────────────────────────────────
    state = fields.Selection(
        [('aprobado', 'APROBADO'), ('pendiente', 'PENDIENTE')],
        string='Estatus', default='pendiente',
        compute='_compute_estado', store=True, tracking=True)

    # ── Columna 5: Revisado por ───────────────────────────────
    revisado_por_id = fields.Many2one('res.users', string='Revisor', readonly=True)
    fecha_revision = fields.Datetime(string='Fecha de revisión', readonly=True)
    revisado_display = fields.Char(
        string='Revisado por', compute='_compute_revisado_display', store=False)

    @api.depends('revisado_por_id', 'fecha_revision')
    def _compute_revisado_display(self):
        for rec in self:
            if rec.revisado_por_id and rec.fecha_revision:
                fecha = fields.Datetime.context_timestamp(
                    rec, rec.fecha_revision).strftime('%d/%m/%Y %H:%M')
                rec.revisado_display = f"{rec.revisado_por_id.name} · {fecha}"
            else:
                rec.revisado_display = ''

    @api.depends('rev_materiales', 'rev_volumenes', 'rev_tiempos')
    def _compute_estado(self):
        for rec in self:
            reviews = [rec.rev_materiales, rec.rev_volumenes, rec.rev_tiempos]
            all_ok = all(r == 'ok' for r in reviews)
            any_fail = any(r == 'fail' for r in reviews)

            rec.state = 'aprobado' if all_ok else 'pendiente'
            rec.obs_requeridas = any_fail
            if all_ok and not rec.observaciones:
                rec.observaciones = 'Ninguna'

    def write(self, vals):
        campos_revision = {'rev_materiales', 'rev_volumenes', 'rev_tiempos'}
        if campos_revision & set(vals):
            vals['revisado_por_id'] = self.env.user.id
            vals['fecha_revision'] = fields.Datetime.now()
        return super().write(vals)
