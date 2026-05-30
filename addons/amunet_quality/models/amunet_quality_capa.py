# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AmunetQualityCAPA(models.Model):
    """
    Acciones Correctivas y Preventivas (CAPA).
    ISO 13485:8.5.2 (Correctiva) y 8.5.3 (Preventiva).
    """
    _name = 'amunet.quality.capa'
    _description = 'Accion Correctiva/Preventiva'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Referencia',
        required=True,
        copy=False,
        readonly=True,
        default='Nuevo'
    )
    title = fields.Char(string='Titulo del Problema', required=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('investigation', 'Investigacion / Causa Raiz'),
        ('action_plan', 'Plan de Accion'),
        ('verification', 'Verificacion de Efectividad'),
        ('closed', 'Cerrado'),
        ('cancel', 'Cancelado')
    ], string='Estado', default='draft', required=True, tracking=True)

    source_check_id = fields.Many2one(
        'amunet.quality.check',
        string='Control de Calidad Origen',
        readonly=True
    )
    product_id = fields.Many2one('product.product', string='Producto', required=True)
    lot_id = fields.Many2one(
        'stock.lot',
        string='Lote',
        domain="[('product_id', '=', product_id)]"
    )
    severity = fields.Selection([
        ('low', 'Baja (Menor)'),
        ('medium', 'Media (Mayor)'),
        ('critical', 'Critica (Seguridad)'),
    ], string='Severidad', default='medium', required=True, tracking=True)

    investigation_notes = fields.Html(
        string='Notas de Investigacion',
        help='Descripcion detallada de la investigacion realizada'
    )
    root_cause = fields.Html(
        string='Causa Raiz',
        help='Analisis de la causa raiz (5 Porques, Ishikawa, etc.)'
    )
    containment_actions = fields.Html(
        string='Acciones de Contencion',
        help='Acciones inmediatas para contener el problema'
    )
    corrective_actions = fields.Html(
        string='Acciones Correctivas',
        help='Acciones a largo plazo para eliminar la causa raiz'
    )
    target_date = fields.Date(string='Fecha Objetivo')
    verification_notes = fields.Html(
        string='Verificacion de Efectividad',
        help='Evidencia de que las acciones eliminaron el problema'
    )
    user_responsible_id = fields.Many2one(
        'res.users',
        string='Responsable',
        default=lambda self: self.env.user,
        tracking=True
    )

    investigation_signed_by_id = fields.Many2one(
        'res.users', string='Investigacion firmada por', readonly=True, copy=False)
    investigation_signed_date = fields.Datetime(
        string='Fecha firma investigacion', readonly=True, copy=False)
    action_plan_signed_by_id = fields.Many2one(
        'res.users', string='Plan firmado por', readonly=True, copy=False)
    action_plan_signed_date = fields.Datetime(
        string='Fecha firma plan', readonly=True, copy=False)
    verification_signed_by_id = fields.Many2one(
        'res.users', string='Verificacion firmada por', readonly=True, copy=False)
    verification_signed_date = fields.Datetime(
        string='Fecha firma verificacion', readonly=True, copy=False)
    closed_by_id = fields.Many2one(
        'res.users', string='Cerrado por', readonly=True, copy=False)
    closed_date = fields.Datetime(
        string='Fecha cierre', readonly=True, copy=False)

    def _signature_fields(self):
        return {
            'investigation_signed_by_id', 'investigation_signed_date',
            'action_plan_signed_by_id', 'action_plan_signed_date',
            'verification_signed_by_id', 'verification_signed_date',
            'closed_by_id', 'closed_date',
        }

    def _has_signature_values(self, vals):
        signature_state = vals.get('state') in (
            'investigation', 'action_plan', 'verification', 'closed')
        return signature_state or self._signature_fields().intersection(vals)

    @api.model_create_multi
    def create(self, vals_list):
        if (
            not self.env.context.get('amunet_capa_signature_write')
            and not self.env.su
        ):
            for vals in vals_list:
                if self._has_signature_values(vals):
                    raise UserError(_(
                        'Las transiciones reguladas de CAPA solo pueden '
                        'registrarse desde el wizard de firma electronica.'))
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('amunet.quality.capa')
                    or 'CAPA-000'
                )
        return super().create(vals_list)

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_action_investigation': _('Iniciar investigacion CAPA'),
            '_signature_action_plan': _('Aprobar plan CAPA'),
            '_signature_action_verification': _('Enviar CAPA a verificacion'),
            '_signature_action_close': _('Cerrar CAPA'),
        }

    def _amunet_signature_required_procedures(self):
        self.ensure_one()
        if self.source_check_id:
            return self.source_check_id.procedure_ids.filtered('active')
        if self.product_id:
            return self.env['amunet.quality.procedure'].search([
                ('active', '=', True),
                ('product_ids', 'in', self.product_id.id),
            ])
        return self.env['amunet.quality.procedure']

    def _open_signature(self, method_name, signature_type, reason):
        self.ensure_one()
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, method_name, signature_type, reason)

    def _check_investigation(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Solo se inicia investigacion desde Borrador.'))

    def action_investigation(self):
        self.ensure_one()
        self._check_investigation()
        return self._open_signature(
            '_signature_action_investigation',
            _('Iniciar investigacion CAPA'),
            _('Firma de inicio de investigacion para %s.') % self.name,
        )

    def _signature_action_investigation(self):
        self.ensure_one()
        self._check_investigation()
        self.with_context(amunet_capa_signature_write=True).write({
            'state': 'investigation',
            'investigation_signed_by_id': self.env.user.id,
            'investigation_signed_date': fields.Datetime.now(),
        })
        return True

    def _check_plan(self):
        for record in self:
            if record.state != 'investigation':
                raise UserError(_('Solo se define plan desde Investigacion.'))
            if not record.root_cause:
                raise UserError(_('Captura la causa raiz antes de firmar el plan.'))
            if not record.corrective_actions:
                raise UserError(_('Captura las acciones correctivas antes de firmar el plan.'))

    def action_plan(self):
        self.ensure_one()
        self._check_plan()
        return self._open_signature(
            '_signature_action_plan',
            _('Aprobar plan CAPA'),
            _('Firma de aprobacion de plan para %s.') % self.name,
        )

    def _signature_action_plan(self):
        self.ensure_one()
        self._check_plan()
        self.with_context(amunet_capa_signature_write=True).write({
            'state': 'action_plan',
            'action_plan_signed_by_id': self.env.user.id,
            'action_plan_signed_date': fields.Datetime.now(),
        })
        return True

    def _check_verification(self):
        for record in self:
            if record.state != 'action_plan':
                raise UserError(_('Solo se envia a verificacion desde Plan de Accion.'))
            if not record.containment_actions:
                raise UserError(_('Captura las acciones de contencion antes de verificar.'))
            if not record.corrective_actions:
                raise UserError(_('Captura las acciones correctivas antes de verificar.'))

    def action_verification(self):
        self.ensure_one()
        self._check_verification()
        return self._open_signature(
            '_signature_action_verification',
            _('Enviar CAPA a verificacion'),
            _('Firma de envio a verificacion para %s.') % self.name,
        )

    def _signature_action_verification(self):
        self.ensure_one()
        self._check_verification()
        self.with_context(amunet_capa_signature_write=True).write({
            'state': 'verification',
            'verification_signed_by_id': self.env.user.id,
            'verification_signed_date': fields.Datetime.now(),
        })
        return True

    def _check_close(self):
        for record in self:
            if record.state != 'verification':
                raise UserError(_('Solo se cierra desde Verificacion de Efectividad.'))
            if not record.verification_notes:
                raise UserError(_('Captura la evidencia de efectividad antes de cerrar.'))

    def action_close(self):
        self.ensure_one()
        self._check_close()
        return self._open_signature(
            '_signature_action_close',
            _('Cerrar CAPA'),
            _('Firma de cierre para %s.') % self.name,
        )

    def _signature_action_close(self):
        self.ensure_one()
        self._check_close()
        self.with_context(amunet_capa_signature_write=True).write({
            'state': 'closed',
            'closed_by_id': self.env.user.id,
            'closed_date': fields.Datetime.now(),
        })
        return True

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def write(self, vals):
        if (
            self._has_signature_values(vals)
            and not self.env.context.get('amunet_capa_signature_write')
            and not self.env.su
        ):
            raise UserError(_(
                'Las transiciones reguladas de CAPA solo pueden registrarse '
                'desde el wizard de firma electronica.'))
        return super().write(vals)
