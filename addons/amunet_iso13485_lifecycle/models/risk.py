from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AmunetRiskAnalysis(models.Model):
    _name = 'amunet.risk.analysis'
    _description = 'Análisis de riesgos ISO 14971 / ISO 13485'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'review_date desc, id desc'

    name = fields.Char(default='Nuevo', readonly=True, copy=False, tracking=True)
    title = fields.Char(required=True, tracking=True)
    product_id = fields.Many2one('product.product', required=True, string='Producto', tracking=True)
    design_project_id = fields.Many2one('amunet.design.project', string='Expediente de diseño', tracking=True)
    state = fields.Selection([
        ('draft', 'Borrador'), ('assessment', 'En evaluación'), ('approved', 'Aprobado'),
        ('review', 'En revisión posterior'), ('closed', 'Cerrado'),
    ], default='draft', required=True, tracking=True)
    scope = fields.Html(string='Alcance y uso previsto', required=True)
    methodology = fields.Html(string='Metodología / criterios de aceptabilidad', required=True)
    review_date = fields.Date(default=fields.Date.today, required=True)
    next_review_date = fields.Date(string='Próxima revisión')
    item_ids = fields.One2many('amunet.risk.item', 'analysis_id', string='Peligros y controles')
    approved_by_id = fields.Many2one('res.users', readonly=True)
    approved_date = fields.Datetime(readonly=True)
    closed_by_id = fields.Many2one('res.users', readonly=True)
    closed_date = fields.Datetime(readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('amunet.risk.analysis') or 'RISK-NUEVO'
        return super().create(vals_list)

    def action_start_assessment(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Solo puede iniciar una evaluación en borrador.'))
            rec.state = 'assessment'

    def action_approve(self):
        for rec in self:
            if rec.state != 'assessment' or not rec.item_ids:
                raise UserError(_('Agregue riesgos antes de aprobar.'))
            unresolved = rec.item_ids.filtered(lambda item: not item.control_verification or item.residual_risk_level == 'unacceptable')
            if unresolved:
                raise UserError(_('Cada riesgo debe tener verificación de control y riesgo residual aceptable.'))
            rec.write({'state': 'approved', 'approved_by_id': self.env.user.id, 'approved_date': fields.Datetime.now()})

    def action_review(self):
        for rec in self:
            if rec.state not in ('approved', 'closed'):
                raise UserError(_('Solo puede revisar un análisis aprobado o cerrado.'))
            rec.state = 'review'

    def action_close(self):
        for rec in self:
            if rec.state not in ('approved', 'review'):
                raise UserError(_('Solo puede cerrar un análisis aprobado.'))
            if rec.item_ids.filtered(lambda item: item.residual_risk_level == 'unacceptable'):
                raise UserError(_('No es posible cerrar con riesgos residuales inaceptables.'))
            rec.write({'state': 'closed', 'closed_by_id': self.env.user.id, 'closed_date': fields.Datetime.now()})


class AmunetRiskItem(models.Model):
    _name = 'amunet.risk.item'
    _description = 'Peligro, control y riesgo residual'
    _order = 'analysis_id, sequence, id'

    analysis_id = fields.Many2one('amunet.risk.analysis', required=True, ondelete='cascade')
    complaint_id = fields.Many2one('amunet.quality.complaint', string='Queja de origen', ondelete='set null')
    sequence = fields.Integer(default=10)
    hazard = fields.Char(string='Peligro', required=True)
    foreseeable_sequence = fields.Html(string='Secuencia de eventos razonablemente previsible', required=True)
    hazardous_situation = fields.Html(string='Situación peligrosa', required=True)
    harm = fields.Html(string='Daño potencial', required=True)
    severity = fields.Selection([(str(i), str(i)) for i in range(1, 6)], default='3', required=True, help='1 mínima — 5 catastrófica')
    probability = fields.Selection([(str(i), str(i)) for i in range(1, 6)], default='3', required=True, help='1 remota — 5 frecuente')
    initial_risk_score = fields.Integer(compute='_compute_scores', store=True)
    initial_risk_level = fields.Selection([('acceptable', 'Aceptable'), ('alarp', 'Reducir cuando sea posible'), ('unacceptable', 'Inaceptable')], compute='_compute_scores', store=True)
    control_measure = fields.Html(string='Medidas de control', required=True)
    control_type = fields.Selection([('inherent', 'Seguridad inherente'), ('protective', 'Protección / proceso'), ('information', 'Información / etiquetado')], required=True, default='inherent')
    control_verification = fields.Html(string='Verificación de efectividad del control')
    residual_severity = fields.Selection([(str(i), str(i)) for i in range(1, 6)], default='3', required=True)
    residual_probability = fields.Selection([(str(i), str(i)) for i in range(1, 6)], default='2', required=True)
    residual_risk_score = fields.Integer(compute='_compute_scores', store=True)
    residual_risk_level = fields.Selection([('acceptable', 'Aceptable'), ('alarp', 'Reducir cuando sea posible'), ('unacceptable', 'Inaceptable')], compute='_compute_scores', store=True)
    benefit_risk_justification = fields.Html(string='Justificación beneficio-riesgo')
    linked_document_id = fields.Many2one('amunet.documento', string='Documento / IFU relacionado')
    change_control_id = fields.Many2one('amunet.change.control', string='Control de cambio')
    design_input_id = fields.Many2one('amunet.design.input', string='Entrada de diseño')
    design_output_id = fields.Many2one('amunet.design.output', string='Salida de diseño')
    capa_id = fields.Many2one('amunet.quality.capa', string='CAPA')
    active = fields.Boolean(default=True)

    @api.depends('severity', 'probability', 'residual_severity', 'residual_probability')
    def _compute_scores(self):
        def level(score):
            return 'acceptable' if score <= 4 else ('alarp' if score <= 9 else 'unacceptable')
        for rec in self:
            rec.initial_risk_score = int(rec.severity) * int(rec.probability)
            rec.initial_risk_level = level(rec.initial_risk_score)
            rec.residual_risk_score = int(rec.residual_severity) * int(rec.residual_probability)
            rec.residual_risk_level = level(rec.residual_risk_score)

    @api.constrains('residual_risk_level', 'benefit_risk_justification')
    def _check_unacceptable_residual(self):
        for rec in self:
            if rec.residual_risk_level == 'unacceptable' and not rec.benefit_risk_justification:
                raise ValidationError(_('Un riesgo residual inaceptable requiere justificación beneficio-riesgo y acciones adicionales.'))
