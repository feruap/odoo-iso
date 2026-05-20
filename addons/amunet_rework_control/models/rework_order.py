# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AmunetReworkOrder(models.Model):
    _name = 'amunet.rework.order'
    _description = 'No conformidad y reproceso de lote'
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
    title = fields.Char(string='Resumen', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('qc_review', 'Revision Calidad'),
        ('approved', 'Reproceso aprobado'),
        ('material_request', 'Material solicitado'),
        ('in_rework', 'En reproceso'),
        ('ready_qc', 'Listo para re-QC'),
        ('retest', 'Re-QC creado'),
        ('closed', 'Cerrado'),
        ('scrap', 'Scrap/Rechazo'),
        ('cancel', 'Cancelado'),
    ], string='Estado', default='draft', required=True, tracking=True)

    origin_quality_check_id = fields.Many2one(
        'amunet.quality.check',
        string='QC que detecto la falla',
        tracking=True,
    )
    production_id = fields.Many2one(
        'mrp.production',
        string='Orden de fabricacion',
        tracking=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        required=True,
        tracking=True,
    )
    lot_id = fields.Many2one(
        'stock.lot',
        string='Lote',
        domain="[('product_id', '=', product_id)]",
        tracking=True,
    )
    lot_name = fields.Char(string='Lote texto', tracking=True)

    qty_nonconforming = fields.Float(
        string='Cantidad no conforme',
        digits='Product Unit of Measure',
        tracking=True,
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='UdM',
        related='product_id.uom_id',
        readonly=True,
    )

    failure_description = fields.Html(
        string='Falla detectada',
        required=True,
        help='Que fallo observo Calidad: migracion, senal, fondo, armado, etc.',
    )
    failed_parameter_summary = fields.Text(
        string='Parametros fallidos',
        help='Resumen del parametro o determinacion que fallo.',
    )
    containment_action = fields.Html(
        string='Contencion / segregacion',
        help='Como se identifica y separa el lote mientras se decide la disposicion.',
    )
    investigation_notes = fields.Html(string='Investigacion')
    risk_assessment = fields.Html(
        string='Evaluacion de riesgo',
        help='Evaluar efecto potencial del reproceso en seguridad/desempeno.',
    )
    disposition = fields.Selection([
        ('rework', 'Reprocesar'),
        ('scrap', 'Rechazar / scrap'),
        ('change_control', 'Requiere control de cambio'),
        ('capa', 'Requiere CAPA'),
    ], string='Disposicion', default='rework', required=True, tracking=True)
    rework_instruction = fields.Html(
        string='Instruccion aprobada de reproceso',
        help='Metodo aprobado: que ajustar, que material usar, controles y limites.',
    )
    permanent_change_required = fields.Boolean(
        string='Puede requerir cambio permanente',
        tracking=True,
    )
    capa_required = fields.Boolean(string='CAPA requerida', tracking=True)

    material_line_ids = fields.One2many(
        'amunet.rework.order.line',
        'rework_id',
        string='Material adicional',
        copy=True,
    )
    material_request_id = fields.Many2one(
        'amunet.material.request',
        string='Solicitud de material',
        readonly=True,
        copy=False,
    )
    material_request_state = fields.Selection(
        related='material_request_id.state',
        string='Estado solicitud material',
        readonly=True,
    )

    qty_reworked = fields.Float(string='Cantidad reprocesada', digits='Product Unit of Measure')
    qty_scrap = fields.Float(string='Cantidad scrap', digits='Product Unit of Measure')
    production_notes = fields.Html(string='Registro de ejecucion Produccion')
    reworked_by_id = fields.Many2one('res.users', string='Reprocesado por', readonly=True)
    reworked_date = fields.Datetime(string='Fecha reproceso', readonly=True)

    reanalysis_check_id = fields.Many2one(
        'amunet.quality.check',
        string='Re-QC / reanalisis',
        readonly=True,
        copy=False,
    )
    reanalysis_result = fields.Selection(
        related='reanalysis_check_id.global_result',
        string='Resultado re-QC',
        readonly=True,
    )
    capa_id = fields.Many2one('amunet.quality.capa', string='CAPA', readonly=True, copy=False)
    change_control_id = fields.Many2one('amunet.change.control', string='Control de cambio', readonly=True, copy=False)

    quality_approved_by_id = fields.Many2one('res.users', string='Aprobo Calidad', readonly=True)
    quality_approved_date = fields.Datetime(string='Fecha aprobacion Calidad', readonly=True)
    closed_by_id = fields.Many2one('res.users', string='Cerrado por', readonly=True)
    closed_date = fields.Datetime(string='Fecha cierre', readonly=True)

    next_step = fields.Char(string='Siguiente paso', compute='_compute_next_step')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'amunet.rework.order'
                ) or 'NCR/Nuevo'
        return super().create(vals_list)

    @api.onchange('origin_quality_check_id')
    def _onchange_origin_quality_check(self):
        for rec in self:
            qc = rec.origin_quality_check_id
            if not qc:
                continue
            rec.product_id = qc.product_id
            rec.lot_id = qc.lot_id
            rec.lot_name = qc.lot_id.name or qc.lot_name_amunet
            rec.qty_nonconforming = qc.qty_sampling or qc.lot_qty_available or 0.0
            rec.failed_parameter_summary = qc.fail_reason
            if not rec.title:
                rec.title = _('Reproceso por falla en %s') % (qc.name or qc.product_id.display_name)

    @api.onchange('production_id')
    def _onchange_production_id(self):
        for rec in self:
            mo = rec.production_id
            if not mo:
                continue
            rec.product_id = mo.product_id
            rec.qty_nonconforming = mo.product_qty
            rec.lot_name = mo.solution_lot_id or ', '.join(mo.lot_producing_ids.mapped('name'))
            if mo.lot_producing_ids:
                rec.lot_id = mo.lot_producing_ids[0]

    @api.depends('state', 'material_request_state', 'reanalysis_result')
    def _compute_next_step(self):
        labels = dict(self._fields['state'].selection)
        for rec in self:
            if rec.state == 'draft':
                rec.next_step = 'Calidad: enviar a revision y documentar falla'
            elif rec.state == 'qc_review':
                rec.next_step = 'Calidad: aprobar reproceso, scrap o abrir CAPA/cambio'
            elif rec.state == 'approved':
                rec.next_step = 'Produccion: solicitar material o iniciar reproceso'
            elif rec.state == 'material_request':
                if rec.material_request_state == 'draft':
                    rec.next_step = 'Produccion: abrir la solicitud de material y dar Firmar y Enviar'
                elif rec.material_request_state in ('submitted', 'in_picking'):
                    rec.next_step = 'Almacen: surtir el material solicitado'
                elif rec.material_request_state == 'pending_reception':
                    rec.next_step = 'Produccion: validar recepcion del material'
                elif rec.material_request_state == 'closed':
                    rec.next_step = 'Produccion: iniciar reproceso'
                else:
                    rec.next_step = 'Produccion y Almacen: completar solicitud de material'
            elif rec.state == 'in_rework':
                rec.next_step = 'Produccion: ejecutar reproceso y marcar listo para re-QC'
            elif rec.state == 'ready_qc':
                rec.next_step = 'Calidad: crear re-QC/reanalisis'
            elif rec.state == 'retest':
                rec.next_step = 'Calidad: completar re-QC y cerrar disposicion'
            elif rec.state in ('closed', 'scrap', 'cancel'):
                rec.next_step = labels.get(rec.state)
            else:
                rec.next_step = ''

    def _require_quality(self):
        if not (
            self.env.user.has_group('amunet_quality.group_quality_supervisor')
            or self.env.user.has_group('amunet_quality.group_quality_manager')
        ):
            raise UserError(_('Solo Supervisor/Manager de Calidad puede ejecutar esta accion.'))

    def _require_production(self):
        if not self.env.user.has_group('amunet_production.group_production_supervisor'):
            raise UserError(_('Solo Supervisor de Produccion puede ejecutar esta accion.'))

    def _require_quality_or_production(self):
        if not (
            self.env.user.has_group('amunet_quality.group_quality_user')
            or self.env.user.has_group('amunet_quality.group_quality_supervisor')
            or self.env.user.has_group('amunet_quality.group_quality_manager')
            or self.env.user.has_group('amunet_production.group_production_supervisor')
        ):
            raise UserError(_('No tiene permisos para crear/enviar no conformidades.'))

    def action_submit_review(self):
        for rec in self:
            rec._require_quality_or_production()
            if rec.state != 'draft':
                raise UserError(_('Solo se envia desde Borrador.'))
            if not rec.failure_description:
                raise UserError(_('Capture la falla detectada.'))
            if not rec.containment_action:
                raise UserError(_('Documente la contencion/segregacion del lote.'))
            rec.write({'state': 'qc_review'})
            rec.message_post(body=_('No conformidad enviada a revision de Calidad.'))

    def action_quality_approve_rework(self):
        for rec in self:
            rec._require_quality()
            if rec.state != 'qc_review':
                raise UserError(_('Solo se aprueba desde Revision Calidad.'))
            if rec.disposition != 'rework':
                raise UserError(_('La disposicion debe ser Reprocesar para aprobar reproceso.'))
            if not rec.rework_instruction:
                raise UserError(_('Capture la instruccion aprobada de reproceso.'))
            if not rec.risk_assessment:
                raise UserError(_('Capture la evaluacion de riesgo antes de aprobar.'))
            rec.write({
                'state': 'approved',
                'quality_approved_by_id': self.env.user.id,
                'quality_approved_date': fields.Datetime.now(),
            })
            rec.message_post(body=_('Calidad aprobo el reproceso.'))

    def action_mark_scrap(self):
        for rec in self:
            rec._require_quality()
            if rec.state not in ('qc_review', 'approved', 'material_request', 'in_rework', 'ready_qc', 'retest'):
                raise UserError(_('No se puede marcar scrap desde este estado.'))
            rec.write({'state': 'scrap', 'disposition': 'scrap'})
            rec.message_post(body=_('Disposicion final: rechazo/scrap.'))

    def action_create_material_request(self):
        for rec in self:
            rec._require_production()
            if rec.state != 'approved':
                raise UserError(_('La solicitud de material requiere reproceso aprobado.'))
            if rec.material_request_id:
                return rec.action_view_material_request()
            if not rec.material_line_ids:
                raise UserError(_('Agregue material adicional antes de solicitar a almacen.'))

            request = self.env['amunet.material.request'].sudo().create({
                'requester_id': self.env.user.id,
                'required_date': fields.Datetime.now(),
                'note': _(
                    'Material para reproceso %(ncr)s. Producto: %(product)s. Lote: %(lot)s.'
                ) % {
                    'ncr': rec.name,
                    'product': rec.product_id.display_name,
                    'lot': rec.lot_name or (rec.lot_id.name if rec.lot_id else ''),
                },
                'line_ids': [(0, 0, {
                    'product_id': line.product_id.id,
                    'qty_requested': line.qty_requested,
                    'lot_id': line.preferred_lot_id.id or False,
                }) for line in rec.material_line_ids],
            })
            rec.write({
                'material_request_id': request.id,
                'state': 'material_request',
            })
            rec.message_post(body=_('Solicitud de material creada: %s.') % request.name)
            return rec.action_view_material_request()

    def action_start_rework(self):
        for rec in self:
            rec._require_production()
            if rec.state not in ('approved', 'material_request'):
                raise UserError(_('Solo se puede iniciar reproceso desde Aprobado o Material solicitado.'))
            if rec.material_line_ids:
                if not rec.material_request_id:
                    raise UserError(_('Primero cree la solicitud de material.'))
                if rec.material_request_state != 'closed':
                    raise UserError(_('El material debe estar surtido y recibido antes de iniciar reproceso.'))
            rec.write({'state': 'in_rework'})
            rec.message_post(body=_('Produccion inicio el reproceso.'))

    def action_ready_for_qc(self):
        for rec in self:
            rec._require_production()
            if rec.state != 'in_rework':
                raise UserError(_('Solo se marca listo desde En reproceso.'))
            if rec.qty_reworked <= 0:
                raise UserError(_('Capture la cantidad reprocesada.'))
            if not rec.production_notes:
                raise UserError(_('Capture el registro de ejecucion de Produccion.'))
            rec.write({
                'state': 'ready_qc',
                'reworked_by_id': self.env.user.id,
                'reworked_date': fields.Datetime.now(),
            })
            rec.message_post(body=_('Produccion marco el lote como listo para re-QC.'))

    def action_create_retest_qc(self):
        for rec in self:
            rec._require_quality()
            if rec.state != 'ready_qc':
                raise UserError(_('El reproceso debe estar listo para re-QC.'))
            if rec.reanalysis_check_id:
                return rec.action_view_reanalysis_check()
            original = rec.origin_quality_check_id
            if original:
                reanalysis_number = original.reanalysis_count + 1
                new_check = original.copy({
                    'name': '%s-RQ%s' % (original.name, reanalysis_number),
                    'parent_check_id': original.id,
                    'analysis_type': 'reanalysis',
                    'reanalysis_count': reanalysis_number,
                    'state': 'draft',
                    'analysis_number': False,
                    'info_reviewed': False,
                    'sampling_confirmed': False,
                    'sampling_move_id': False,
                    'qty_sampling': rec.qty_reworked,
                    'sampling_uom_id': rec.uom_id.id,
                    'qty_analyzed': 0,
                    'user_realized_id': False,
                    'user_verified_id': False,
                    'user_authorized_id': False,
                    'reviewed_by_id': False,
                    'reviewed_date': False,
                    'sampling_date': False,
                    'analysis_date': False,
                })
            else:
                new_check = self.env['amunet.quality.check'].create({
                    'product_id': rec.product_id.id,
                    'lot_id': rec.lot_id.id or False,
                    'requester_id': self.env.user.id,
                    'qty_sampling': rec.qty_reworked,
                    'sampling_uom_id': rec.uom_id.id,
                    'analysis_type': 'reanalysis',
                })
            rec.write({
                'reanalysis_check_id': new_check.id,
                'state': 'retest',
            })
            rec.message_post(body=_('Re-QC creado: %s.') % new_check.name)
            new_check.message_post(body=_('Re-QC creado desde no conformidad/reproceso %s.') % rec.name)
            return rec.action_view_reanalysis_check()

    def action_close(self):
        for rec in self:
            rec._require_quality()
            if rec.state != 'retest':
                raise UserError(_('Solo se cierra despues de crear re-QC.'))
            if not rec.reanalysis_check_id:
                raise UserError(_('Falta el re-QC.'))
            if rec.reanalysis_check_id.state != 'done' or rec.reanalysis_check_id.global_result != 'pass':
                raise UserError(_('El re-QC debe estar finalizado y aprobado para cerrar. Si falla, marque scrap o abra CAPA.'))
            rec.write({
                'state': 'closed',
                'closed_by_id': self.env.user.id,
                'closed_date': fields.Datetime.now(),
            })
            rec.message_post(body=_('No conformidad/reproceso cerrado con re-QC aprobado.'))

    def action_create_capa(self):
        for rec in self:
            rec._require_quality()
            if rec.capa_id:
                return rec.action_view_capa()
            capa = self.env['amunet.quality.capa'].create({
                'source_check_id': rec.origin_quality_check_id.id or False,
                'product_id': rec.product_id.id,
                'lot_id': rec.lot_id.id or False,
                'title': _('CAPA por no conformidad %s') % rec.name,
                'severity': 'medium',
                'investigation_notes': rec.failure_description,
                'containment_actions': rec.containment_action,
            })
            rec.write({'capa_id': capa.id, 'capa_required': True})
            rec.message_post(body=_('CAPA creada: %s.') % capa.name)
            return rec.action_view_capa()

    def action_create_change_control(self):
        for rec in self:
            rec._require_quality()
            if rec.change_control_id:
                return rec.action_view_change_control()
            cc = self.env['amunet.change.control'].create({
                'title': _('Cambio por no conformidad %s') % rec.name,
                'request_type': 'material_substitution',
                'scope': 'product' if rec.permanent_change_required else 'lot',
                'product_id': rec.product_id.id,
                'lot_id': rec.lot_id.id or False,
                'production_id': rec.production_id.id or False,
                'quality_check_id': rec.origin_quality_check_id.id or False,
                'rationale': rec.failure_description,
                'risk_assessment': rec.risk_assessment,
                'disposition': rec.rework_instruction,
            })
            rec.write({'change_control_id': cc.id, 'permanent_change_required': True})
            rec.message_post(body=_('Control de cambio creado: %s.') % cc.name)
            return rec.action_view_change_control()

    def action_view_material_request(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Solicitud de material'),
            'res_model': 'amunet.material.request',
            'view_mode': 'form',
            'res_id': self.material_request_id.id,
        }

    def action_view_reanalysis_check(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Re-QC'),
            'res_model': 'amunet.quality.check',
            'view_mode': 'form',
            'res_id': self.reanalysis_check_id.id,
        }

    def action_view_capa(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('CAPA'),
            'res_model': 'amunet.quality.capa',
            'view_mode': 'form',
            'res_id': self.capa_id.id,
        }

    def action_view_change_control(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Control de cambio'),
            'res_model': 'amunet.change.control',
            'view_mode': 'form',
            'res_id': self.change_control_id.id,
        }


class AmunetReworkOrderLine(models.Model):
    _name = 'amunet.rework.order.line'
    _description = 'Material para reproceso'
    _order = 'id'

    rework_id = fields.Many2one(
        'amunet.rework.order',
        string='Reproceso',
        required=True,
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        'product.product',
        string='Material',
        required=True,
        domain="[('is_storable', '=', True)]",
    )
    qty_requested = fields.Float(
        string='Cantidad requerida',
        default=1.0,
        digits='Product Unit of Measure',
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='UdM',
        related='product_id.uom_id',
        readonly=True,
    )
    preferred_lot_id = fields.Many2one(
        'stock.lot',
        string='Lote sugerido',
        domain="[('product_id', '=', product_id)]",
    )
    reason = fields.Char(string='Uso / justificacion')

    @api.constrains('qty_requested')
    def _check_qty_requested(self):
        for rec in self:
            if rec.qty_requested <= 0:
                raise ValidationError(_('La cantidad requerida debe ser mayor a cero.'))
