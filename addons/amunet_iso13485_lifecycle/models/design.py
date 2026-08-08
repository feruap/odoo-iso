from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AmunetDesignProject(models.Model):
    _name = 'amunet.design.project'
    _description = 'Expediente de diseño y desarrollo ISO 13485'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(default='Nuevo', readonly=True, copy=False, tracking=True)
    title = fields.Char(required=True, tracking=True)
    product_id = fields.Many2one('product.product', required=True, string='Producto', tracking=True)
    state = fields.Selection([
        ('planning', 'Planificación'), ('inputs', 'Entradas'), ('outputs', 'Salidas'),
        ('verification', 'Verificación'), ('validation', 'Validación'),
        ('transfer', 'Transferencia'), ('released', 'Liberado'), ('closed', 'Cerrado'),
    ], default='planning', required=True, tracking=True)
    intended_use = fields.Html(string='Uso previsto', required=True)
    design_plan = fields.Html(string='Plan de diseño')
    input_ids = fields.One2many('amunet.design.input', 'project_id', string='Entradas de diseño')
    output_ids = fields.One2many('amunet.design.output', 'project_id', string='Salidas de diseño')
    verification_ids = fields.One2many('amunet.design.verification', 'project_id', string='Verificación y validación')
    risk_analysis_ids = fields.One2many('amunet.risk.analysis', 'design_project_id', string='Análisis de riesgos')
    source_document_id = fields.Many2one('amunet.documento', string='Documento de origen')
    transfer_document_id = fields.Many2one('amunet.documento', string='Documento de transferencia / DMR')
    change_control_id = fields.Many2one('amunet.change.control', string='Control de cambio')
    transfer_evidence = fields.Html(string='Evidencia de transferencia')
    transfer_date = fields.Datetime(readonly=True)
    transferred_by_id = fields.Many2one('res.users', readonly=True)
    released_by_id = fields.Many2one('res.users', readonly=True)
    released_date = fields.Datetime(readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('amunet.design.project') or 'DIS-NUEVO'
        return super().create(vals_list)

    def _advance(self, expected, target, required=()):
        for rec in self:
            if rec.state != expected:
                raise UserError(_('Transición no permitida desde el estado actual.'))
            missing = [label for field, label in required if not getattr(rec, field)]
            if missing:
                raise UserError(_('Falta completar: %s') % ', '.join(missing))
            rec.write({'state': target})

    def action_confirm_inputs(self):
        self._advance('planning', 'inputs', [('design_plan', _('plan de diseño'))])
    def action_confirm_outputs(self):
        self._advance('inputs', 'outputs', [('input_ids', _('al menos una entrada de diseño'))])
    def action_verify(self):
        self._advance('outputs', 'verification', [('output_ids', _('al menos una salida de diseño'))])
    def action_validate(self):
        for rec in self:
            if rec.state != 'verification' or not rec.verification_ids.filtered(lambda x: x.stage == 'verification' and x.result == 'pass'):
                raise UserError(_('Registre una verificación aprobada antes de validar.'))
            rec.state = 'validation'
    def action_transfer(self):
        for rec in self:
            if rec.state != 'validation' or not rec.verification_ids.filtered(lambda x: x.stage == 'validation' and x.result == 'pass'):
                raise UserError(_('Registre una validación aprobada antes de transferir.'))
            if not rec.transfer_document_id or not rec.transfer_evidence:
                raise UserError(_('La transferencia requiere documento controlado y evidencia.'))
            rec.write({'state': 'transfer', 'transfer_date': fields.Datetime.now(), 'transferred_by_id': self.env.user.id})
    def action_release(self):
        for rec in self:
            if rec.state != 'transfer':
                raise UserError(_('Solo puede liberarse un diseño transferido.'))
            rec.write({'state': 'released', 'released_by_id': self.env.user.id, 'released_date': fields.Datetime.now()})


class AmunetDesignInput(models.Model):
    _name = 'amunet.design.input'
    _description = 'Entrada de diseño'
    _order = 'sequence, id'
    project_id = fields.Many2one('amunet.design.project', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True, string='Requisito')
    source = fields.Selection([('user', 'Usuario'), ('regulatory', 'Regulatorio'), ('risk', 'Riesgo'), ('standard', 'Norma'), ('other', 'Otro')], required=True, default='user')
    acceptance_criteria = fields.Text(required=True)
    document_id = fields.Many2one('amunet.documento', string='Documento fuente')
    output_ids = fields.Many2many('amunet.design.output', 'amunet_design_input_output_rel', 'input_id', 'output_id', string='Salidas que satisfacen')


class AmunetDesignOutput(models.Model):
    _name = 'amunet.design.output'
    _description = 'Salida de diseño'
    _order = 'sequence, id'
    project_id = fields.Many2one('amunet.design.project', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)
    description = fields.Html(required=True)
    output_type = fields.Selection([('specification', 'Especificación'), ('drawing', 'Plano'), ('bom', 'BOM'), ('procedure', 'Procedimiento'), ('label', 'Etiqueta / IFU'), ('other', 'Otro')], required=True, default='specification')
    document_id = fields.Many2one('amunet.documento', string='Documento controlado')
    approved = fields.Boolean(default=False)


class AmunetDesignVerification(models.Model):
    _name = 'amunet.design.verification'
    _description = 'Verificación / validación de diseño'
    _order = 'date desc, id desc'
    project_id = fields.Many2one('amunet.design.project', required=True, ondelete='cascade')
    stage = fields.Selection([('verification', 'Verificación'), ('validation', 'Validación')], required=True)
    name = fields.Char(required=True, string='Protocolo / prueba')
    method = fields.Html(string='Método', required=True)
    acceptance_criteria = fields.Html(string='Criterios de aceptación', required=True)
    result = fields.Selection([('pending', 'Pendiente'), ('pass', 'Aprobada'), ('fail', 'No aprobada')], default='pending', required=True)
    evidence = fields.Html(string='Evidencia / resultados')
    date = fields.Date(default=fields.Date.today)
    responsible_id = fields.Many2one('res.users', default=lambda self: self.env.user)
