# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AmunetChangeControl(models.Model):
    _name = 'amunet.change.control'
    _description = 'Desviacion y Control de Cambios'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(
        string='Folio',
        default='Nuevo',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
    )
    title = fields.Char(string='Titulo', required=True, tracking=True)

    request_type = fields.Selection([
        ('material_substitution', 'Insumo no conforme / sustitucion controlada'),
        ('lot_instruction_change', 'Condicion especial de uso por lote'),
        ('document_change', 'Cambio documental permanente'),
        ('print_request', 'Solicitud de impresion controlada'),
        ('other', 'Otro'),
    ], string='Tipo', required=True, default='material_substitution', tracking=True)

    scope = fields.Selection([
        ('lot', 'Solo este lote'),
        ('product', 'Producto / siguientes lotes'),
        ('permanent', 'Cambio permanente'),
    ], string='Alcance', required=True, default='lot', tracking=True)

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('evaluation', 'En evaluacion'),
        ('quality_approved', 'Aprobado Calidad'),
        ('sanitary_approved', 'Aprobado Responsable'),
        ('documentation_ready', 'Documentacion lista'),
        ('print_requested', 'Impresion solicitada'),
        ('implemented', 'Implementado'),
        ('closed', 'Cerrado'),
        ('rejected', 'Rechazado'),
        ('cancel', 'Cancelado'),
    ], string='Estado', default='draft', required=True, tracking=True)

    product_id = fields.Many2one(
        'product.product',
        string='Producto afectado',
        required=True,
        tracking=True,
    )
    lot_id = fields.Many2one(
        'stock.lot',
        string='Lote afectado',
        domain="[('product_id', '=', product_id)]",
        tracking=True,
    )
    production_id = fields.Many2one(
        'mrp.production',
        string='Orden de produccion',
        tracking=True,
    )
    quality_check_id = fields.Many2one(
        'amunet.quality.check',
        string='Control de calidad',
        tracking=True,
    )
    picking_id = fields.Many2one('stock.picking', string='Recepcion / traslado')

    original_material_id = fields.Many2one(
        'product.product',
        string='Insumo original',
        help='Insumo que no funciona, no cumple o sera sustituido.',
    )
    substitute_material_id = fields.Many2one(
        'product.product',
        string='Insumo sustituto / solucion interna',
        help='Insumo aprobado para uso controlado.',
    )

    current_instruction = fields.Text(
        string='Instruccion vigente',
        help='Ejemplo: usar 3 gotas de sangre.',
    )
    proposed_instruction = fields.Text(
        string='Instruccion propuesta',
        help='Ejemplo: para este lote usar 4 gotas de sangre.',
    )
    rationale = fields.Html(string='Justificacion / evidencia', required=True)
    risk_assessment = fields.Html(string='Evaluacion de riesgo')
    disposition = fields.Html(string='Disposicion / decision')

    source_document_id = fields.Many2one(
        'amunet.quality.procedure',
        string='Documento vigente / origen',
        help='Manual, instructivo, etiqueta o SOP vigente antes del cambio.',
    )
    target_document_id = fields.Many2one(
        'amunet.quality.procedure',
        string='Nueva version / addendum aprobado',
        help='Nueva version permanente o addendum temporal aprobado.',
    )
    document_change_required = fields.Boolean(
        string='Requiere cambio documental',
        tracking=True,
    )
    document_change_scope = fields.Selection([
        ('none', 'No aplica'),
        ('lot_addendum', 'Addendum solo para lote'),
        ('permanent_revision', 'Nueva version permanente'),
    ], string='Tipo de documento', default='none', tracking=True)

    print_required = fields.Boolean(string='Requiere impresion', tracking=True)
    print_quantity = fields.Integer(string='Cantidad a imprimir')
    print_description = fields.Text(
        string='Instruccion de impresion',
        help='Ejemplo: imprimir 70 instructivos addendum para lote X.',
    )
    print_status = fields.Selection([
        ('not_required', 'No requerido'),
        ('pending', 'Pendiente'),
        ('requested', 'Solicitado'),
        ('done', 'Impreso / entregado'),
    ], string='Estado impresion', default='not_required', tracking=True)

    requested_by_id = fields.Many2one(
        'res.users',
        string='Solicitado por',
        default=lambda self: self.env.user,
        readonly=True,
        tracking=True,
    )
    quality_approved_by_id = fields.Many2one(
        'res.users',
        string='Aprobo Calidad',
        readonly=True,
        tracking=True,
    )
    quality_approved_date = fields.Datetime(string='Fecha aprobacion Calidad', readonly=True)
    sanitary_approved_by_id = fields.Many2one(
        'res.users',
        string='Aprobo Responsable',
        readonly=True,
        tracking=True,
    )
    sanitary_approved_date = fields.Datetime(string='Fecha aprobacion Responsable', readonly=True)
    documentation_user_id = fields.Many2one(
        'res.users',
        string='Documentacion',
        tracking=True,
    )
    implemented_by_id = fields.Many2one('res.users', string='Implementado por', readonly=True)
    implemented_date = fields.Datetime(string='Fecha implementacion', readonly=True)
    effective_date = fields.Date(string='Fecha efectiva')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'amunet.change.control'
                ) or 'DCC/Nuevo'
        return super().create(vals_list)

    @api.constrains('print_quantity')
    def _check_print_quantity(self):
        for record in self:
            if record.print_quantity and record.print_quantity < 0:
                raise ValidationError(_('La cantidad a imprimir no puede ser negativa.'))

    @api.onchange('request_type', 'scope')
    def _onchange_request_type(self):
        for record in self:
            if record.request_type == 'lot_instruction_change':
                record.document_change_required = True
                if record.document_change_scope == 'none':
                    record.document_change_scope = 'lot_addendum'
            elif record.request_type == 'document_change':
                record.scope = 'permanent'
                record.document_change_required = True
                record.document_change_scope = 'permanent_revision'
            elif record.request_type == 'print_request':
                record.print_required = True
                if record.print_status == 'not_required':
                    record.print_status = 'pending'

    def _require(self, condition, message):
        if not condition:
            raise UserError(message)

    def _has_any_group(self, group_xmlids):
        return any(self.env.user.has_group(group) for group in group_xmlids)

    def _require_any_group(self, group_xmlids, message):
        if not self._has_any_group(group_xmlids):
            raise UserError(message)

    def action_submit(self):
        for record in self:
            record._require_any_group([
                'amunet_quality.group_quality_user',
                'amunet_quality.group_quality_supervisor',
                'amunet_quality.group_quality_manager',
                'amunet_production.group_production_supervisor',
                'amunet_change_control.group_change_control_documentation',
            ], _('No tiene permisos para enviar desviaciones/cambios a evaluacion.'))
            record._require(record.product_id, _('Seleccione el producto afectado.'))
            record._require(record.rationale, _('Capture la justificacion/evidencia.'))
            if record.scope == 'lot':
                record._require(record.lot_id or record.production_id or record.quality_check_id,
                                _('Para alcance de lote vincule lote, orden o QC.'))
            if record.request_type == 'material_substitution':
                record._require(record.original_material_id,
                                _('Indique el insumo original que no cumple o sera sustituido.'))
            if record.request_type == 'lot_instruction_change':
                record._require(record.proposed_instruction,
                                _('Capture la instruccion propuesta para el lote.'))
            if record.request_type == 'document_change':
                record._require(record.source_document_id,
                                _('Indique el documento vigente que se va a cambiar.'))
            record.write({'state': 'evaluation'})
            record.message_post(body=_('Solicitud enviada a evaluacion.'))

    def action_quality_approve(self):
        for record in self:
            record._require_any_group([
                'amunet_quality.group_quality_supervisor',
                'amunet_quality.group_quality_manager',
            ], _('Solo Supervisor QC o Manager QC puede aprobar por Calidad.'))
            record._require(record.state == 'evaluation',
                            _('Solo se puede aprobar Calidad desde En evaluacion.'))
            record.write({
                'state': 'quality_approved',
                'quality_approved_by_id': self.env.user.id,
                'quality_approved_date': fields.Datetime.now(),
            })
            record.message_post(body=_('Calidad aprobo la desviacion/cambio.'))

    def action_sanitary_approve(self):
        for record in self:
            record._require_any_group([
                'amunet_quality.group_quality_sanitary',
                'amunet_quality.group_quality_manager',
            ], _('Solo Responsable Sanitario o Manager QC puede autorizar.'))
            record._require(record.state == 'quality_approved',
                            _('Primero debe aprobar Calidad.'))
            record.write({
                'state': 'sanitary_approved',
                'sanitary_approved_by_id': self.env.user.id,
                'sanitary_approved_date': fields.Datetime.now(),
            })
            record.message_post(body=_('Responsable autorizado aprobo la desviacion/cambio.'))

    def action_documentation_ready(self):
        for record in self:
            record._require_any_group([
                'amunet_change_control.group_change_control_documentation',
                'amunet_quality.group_quality_supervisor',
                'amunet_quality.group_quality_manager',
            ], _('Solo Documentacion o Calidad autorizada puede liberar documentacion.'))
            record._require(record.state in ('quality_approved', 'sanitary_approved'),
                            _('La solicitud debe estar aprobada antes de liberar documentacion.'))
            if record.document_change_required:
                record._require(record.target_document_id,
                                _('Vincule la nueva version documental o addendum aprobado.'))
            record.write({'state': 'documentation_ready'})
            record.message_post(body=_('Documentacion marco el documento como listo.'))

    def action_request_print(self):
        for record in self:
            record._require_any_group([
                'amunet_change_control.group_change_control_documentation',
                'amunet_quality.group_quality_supervisor',
                'amunet_quality.group_quality_manager',
            ], _('Solo Documentacion o Calidad autorizada puede solicitar impresion.'))
            record._require(record.state in ('sanitary_approved', 'documentation_ready'),
                            _('La impresion requiere aprobacion previa.'))
            record._require(record.print_required, _('Active Requiere impresion.'))
            record._require(record.print_quantity and record.print_quantity > 0,
                            _('Capture la cantidad a imprimir.'))
            record.write({
                'state': 'print_requested',
                'print_status': 'requested',
            })
            record.message_post(
                body=_('Impresion solicitada: %s pieza(s).') % record.print_quantity
            )

    def action_mark_print_done(self):
        for record in self:
            record._require_any_group([
                'amunet_change_control.group_change_control_documentation',
                'amunet_quality.group_quality_supervisor',
                'amunet_quality.group_quality_manager',
            ], _('Solo Documentacion o Calidad autorizada puede cerrar la impresion.'))
            record._require(record.print_status == 'requested',
                            _('La impresion debe estar solicitada.'))
            record.write({'print_status': 'done'})
            record.message_post(body=_('Impresion marcada como completada/entregada.'))

    def action_implement(self):
        for record in self:
            record._require_any_group([
                'amunet_production.group_production_supervisor',
                'amunet_quality.group_quality_supervisor',
                'amunet_quality.group_quality_manager',
            ], _('Solo Produccion autorizada o Calidad puede implementar el cambio.'))
            record._require(record.state in ('sanitary_approved', 'documentation_ready', 'print_requested'),
                            _('La solicitud debe estar aprobada antes de implementar.'))
            if record.print_required:
                record._require(record.print_status == 'done',
                                _('No se puede implementar hasta cerrar la impresion.'))
            record.write({
                'state': 'implemented',
                'implemented_by_id': self.env.user.id,
                'implemented_date': fields.Datetime.now(),
            })
            record.message_post(body=_('Cambio/desviacion implementado.'))

    def action_close(self):
        for record in self:
            record._require_any_group([
                'amunet_quality.group_quality_supervisor',
                'amunet_quality.group_quality_manager',
            ], _('Solo Supervisor QC o Manager QC puede cerrar la solicitud.'))
            record._require(record.state == 'implemented',
                            _('Solo se puede cerrar despues de implementar.'))
            record.write({'state': 'closed'})
            record.message_post(body=_('Solicitud cerrada.'))

    def action_reject(self):
        self._require_any_group([
            'amunet_quality.group_quality_supervisor',
            'amunet_quality.group_quality_sanitary',
            'amunet_quality.group_quality_manager',
        ], _('Solo Calidad autorizada puede rechazar la solicitud.'))
        self.write({'state': 'rejected'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_view_quality_check(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Control de calidad'),
            'res_model': 'amunet.quality.check',
            'view_mode': 'form',
            'res_id': self.quality_check_id.id,
        }

    def action_view_production(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Orden de produccion'),
            'res_model': 'mrp.production',
            'view_mode': 'form',
            'res_id': self.production_id.id,
        }
