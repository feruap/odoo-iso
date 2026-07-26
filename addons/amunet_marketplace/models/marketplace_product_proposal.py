from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MarketplaceProductProposal(models.Model):
    _name = 'amunet.marketplace.product.proposal'
    _description = 'Propuesta de producto para marketplace'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(string='Producto propuesto', required=True, tracking=True)
    requester_id = fields.Many2one(
        'res.users',
        string='Solicitante',
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Area',
        compute='_compute_department_id',
        store=True,
        readonly=False,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Borrador'),
            ('submitted', 'En revision'),
            ('approved', 'Aprobada'),
            ('rejected', 'Rechazada'),
            ('converted', 'Convertida a producto'),
        ],
        string='Estado',
        default='draft',
        required=True,
        tracking=True,
    )
    request_type = fields.Selection(
        selection=[
            ('general', 'Compra general'),
            ('production', 'Produccion / fabricacion'),
        ],
        string='Tipo sugerido',
        default='general',
        required=True,
        tracking=True,
    )
    category_id = fields.Many2one('product.category', string='Categoria sugerida', tracking=True)
    purchase_url = fields.Char(string='URL sugerida', tracking=True)
    image_1920 = fields.Image(string='Imagen')
    justification = fields.Text(string='Justificacion', required=True)
    manager_notes = fields.Text(string='Notas de compras / administrador')
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Producto creado',
        readonly=True,
        copy=False,
    )
    is_material_manager_for_user = fields.Boolean(
        compute='_compute_is_material_manager_for_user',
        help='True si el usuario actual puede gestionar la propuesta.',
    )

    @api.depends('requester_id')
    def _compute_department_id(self):
        for rec in self:
            if rec.department_id:
                continue
            emp = self.env['hr.employee'].sudo().search([('user_id', '=', rec.requester_id.id)], limit=1)
            rec.department_id = emp.department_id.id if emp else False

    @api.depends_context('uid')
    def _compute_is_material_manager_for_user(self):
        allowed = self.env.user.has_group('amunet_material_request.group_material_manager')
        for rec in self:
            rec.is_material_manager_for_user = allowed

    def _check_can_manage(self):
        if not self.env.user.has_group('amunet_material_request.group_material_manager'):
            raise UserError(_('Solo el administrador de Solicitudes de Material puede gestionar propuestas.'))

    def _check_manual_write(self, vals):
        if self.env.context.get('marketplace_proposal_internal_write'):
            return
        protected = {'state', 'manager_notes', 'product_tmpl_id'}
        if not vals:
            return
        if self.env.user.has_group('amunet_material_request.group_material_manager'):
            return
        if protected.intersection(vals):
            raise UserError(_(
                'No puedes modificar el estado, las notas de compras ni el producto creado de una propuesta.'
            ))
        for rec in self:
            if rec.requester_id != self.env.user:
                raise UserError(_('Solo puedes modificar tus propias propuestas.'))
            if rec.state != 'draft':
                raise UserError(_('Solo puedes modificar propuestas en borrador.'))

    def action_submit(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Solo se pueden enviar propuestas en borrador.'))
            rec.with_context(marketplace_proposal_internal_write=True).write({
                'state': 'submitted',
            })
        return True

    def action_reject(self):
        self._check_can_manage()
        for rec in self:
            if rec.state not in ('submitted', 'approved'):
                raise UserError(_('Solo se pueden rechazar propuestas en revision o aprobadas.'))
            rec.with_context(marketplace_proposal_internal_write=True).write({
                'state': 'rejected',
            })
        return True

    def action_approve(self):
        self._check_can_manage()
        for rec in self:
            if rec.state != 'submitted':
                raise UserError(_('Solo se pueden aprobar propuestas en revision.'))
            rec.with_context(marketplace_proposal_internal_write=True).write({
                'state': 'approved',
            })
        return True

    def action_create_product(self):
        self._check_can_manage()
        ProductTemplate = self.env['product.template'].sudo()
        for rec in self:
            if rec.state != 'approved':
                raise UserError(_('La propuesta debe estar aprobada antes de crear el producto.'))
            vals = {
                'name': rec.name,
                'marketplace_enabled': True,
                'marketplace_flow': rec.request_type,
                'marketplace_purchase_url': rec.purchase_url,
                'image_1920': rec.image_1920,
                'purchase_ok': True,
                'sale_ok': False,
                'is_storable': True,
            }
            if rec.category_id:
                vals['categ_id'] = rec.category_id.id
            else:
                raise UserError(_('La propuesta debe indicar una categoria antes de crear el producto.'))
            product = ProductTemplate.create(vals)
            rec.with_context(marketplace_proposal_internal_write=True).write({
                'product_tmpl_id': product.id,
                'state': 'converted',
            })
        return True

    def write(self, vals):
        self._check_manual_write(vals)
        return super().write(vals)
