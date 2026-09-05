from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from .risk_analysis import NIVEL_SELECTION, _nivel_npr


class AmunetRiskReanalysis(models.Model):
    _name = 'amunet.risk.reanalysis'
    _description = 'Re-análisis de Riesgos (Post-control)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha desc, id desc'

    name = fields.Char(string='Folio', readonly=True, copy=False, default='Nuevo')
    analisis_id = fields.Many2one(
        'amunet.risk.analysis', string='Análisis original',
        required=True, tracking=True,
        domain=[('state', '=', 'aprobado')])
    fecha = fields.Date(
        string='Fecha de re-análisis', default=fields.Date.today, required=True, tracking=True)
    responsable_id = fields.Many2one(
        'res.users', string='Responsable',
        default=lambda self: self.env.user, required=True, tracking=True)
    acciones_implementadas = fields.Text(
        string='Acciones implementadas', help='Describe las acciones aplicadas desde el análisis original.')
    conclusion = fields.Text(string='Conclusión general del re-análisis')

    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('aprobado', 'Aprobado'),
    ], string='Estado', default='borrador', tracking=True)

    linea_ids = fields.One2many(
        'amunet.risk.reanalysis.linea', 're_analisis_id', string='Líneas re-analizadas')

    firma_id = fields.Many2one('res.users', string='Aprobó', readonly=True)
    fecha_firma = fields.Datetime(string='Fecha de aprobación', readonly=True)

    total_lineas = fields.Integer(compute='_compute_resumen', store=True)
    total_alto = fields.Integer(compute='_compute_resumen', store=True, string='Alto riesgo residual')
    total_medio = fields.Integer(compute='_compute_resumen', store=True, string='Riesgo medio residual')

    criteria_ids = fields.Many2many(
        'amunet.risk.matrix', compute='_compute_criteria', string='Criterios NPR')

    def _compute_criteria(self):
        criterios = self.env['amunet.risk.matrix'].search([], order='npr_min')
        for rec in self:
            rec.criteria_ids = criterios

    @api.depends('linea_ids.nivel_riesgo')
    def _compute_resumen(self):
        for rec in self:
            rec.total_lineas = len(rec.linea_ids)
            rec.total_alto = len(rec.linea_ids.filtered(lambda l: l.nivel_riesgo == 'alto'))
            rec.total_medio = len(rec.linea_ids.filtered(lambda l: l.nivel_riesgo == 'medio'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'amunet.risk.reanalysis') or 'Nuevo'
        return super().create(vals_list)

    def action_aprobar(self):
        self.ensure_one()
        if not self.linea_ids:
            raise UserError('Agrega al menos una línea de re-análisis antes de aprobar.')
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_aprobar', 'Aprobación del re-análisis de riesgos')

    def _signature_aprobar(self):
        self.ensure_one()
        self.write({
            'state': 'aprobado',
            'firma_id': self.env.user.id,
            'fecha_firma': fields.Datetime.now(),
        })

    def _amunet_signature_allowed_methods(self):
        return {'_signature_aprobar': 'Aprobación del re-análisis de riesgos'}


class AmunetRiskReanalysisLinea(models.Model):
    _name = 'amunet.risk.reanalysis.linea'
    _description = 'Línea de Re-análisis'
    _order = 're_analisis_id, sequence, id'

    re_analisis_id = fields.Many2one(
        'amunet.risk.reanalysis', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)

    linea_original_id = fields.Many2one(
        'amunet.risk.analysis.linea', string='Modo de falla original',
        domain="[('analisis_id', '=', parent.analisis_id)]")
    elemento = fields.Char(
        related='linea_original_id.elemento', string='Elemento / Función', readonly=True)
    modo_falla = fields.Char(
        related='linea_original_id.modo_falla', string='Modo de falla', readonly=True)

    npm_original = fields.Integer(
        related='linea_original_id.npm', string='NPR original', readonly=True)
    nivel_original = fields.Selection(
        NIVEL_SELECTION, related='linea_original_id.nivel_riesgo', string='Nivel original', readonly=True)

    severidad = fields.Integer(
        string='Nueva S', default=1,
        help="Severidad del efecto si el fallo ocurre (1 = mínima, 5 = máxima):\n"
             "1 — Sin impacto perceptible\n"
             "2 — Impacto menor, detectable internamente\n"
             "3 — Efecto moderado, requiere reproceso\n"
             "4 — Efecto grave, puede afectar la calidad del resultado\n"
             "5 — Crítico: riesgo para el paciente o incumplimiento regulatorio")
    ocurrencia = fields.Integer(
        string='Nueva O', default=1,
        help="Frecuencia con que ocurre la causa del fallo (1 = muy rara, 5 = muy frecuente):\n"
             "1 — Muy improbable (nunca ha ocurrido)\n"
             "2 — Remota (una vez en varios años)\n"
             "3 — Ocasional (algunas veces al año)\n"
             "4 — Frecuente (varias veces al mes)\n"
             "5 — Muy frecuente (ocurre regularmente)")
    detectabilidad = fields.Integer(
        string='Nueva D', default=1,
        help="Probabilidad de NO detectar el fallo antes de que llegue al siguiente paso o al cliente\n"
             "(1 = casi seguro que se detecta, 5 = prácticamente indetectable):\n"
             "1 — Detección casi segura (controles robustos, 100% automatizados)\n"
             "2 — Alta probabilidad de detección\n"
             "3 — Probabilidad media de detección\n"
             "4 — Baja probabilidad de detección\n"
             "5 — Sin control de detección existente")

    npm = fields.Integer(string='NPR residual', compute='_compute_npr', store=True)
    nivel_riesgo = fields.Selection(
        NIVEL_SELECTION, string='Nivel residual', compute='_compute_npr', store=True)

    conclusion = fields.Char(string='Conclusión')

    @api.depends('severidad', 'ocurrencia', 'detectabilidad')
    def _compute_npr(self):
        for rec in self:
            s = rec.severidad or 0
            o = rec.ocurrencia or 0
            d = rec.detectabilidad or 0
            rec.npm = s * o * d
            rec.nivel_riesgo = _nivel_npr(rec.npm)

    @api.constrains('severidad', 'ocurrencia', 'detectabilidad')
    def _check_escala(self):
        for rec in self:
            for campo, val in [('Severidad', rec.severidad),
                               ('Ocurrencia', rec.ocurrencia),
                               ('Detectabilidad', rec.detectabilidad)]:
                if val and not (1 <= val <= 5):
                    raise ValidationError(_('{} debe estar entre 1 y 5.').format(campo))
