# -*- coding: utf-8 -*-

import hashlib
import json

from markupsafe import Markup

from odoo import models, fields, api
from odoo.exceptions import UserError


class StockLot(models.Model):
    """
    Extensión de stock.lot para integrar reanálisis desde Inventario.

    Permite a los usuarios de inventario visualizar los controles de calidad
    asociados a un lote y solicitar un reanálisis directamente desde el
    formulario de lote, sin necesidad de acceder al módulo de Calidad.
    """
    _inherit = 'stock.lot'

    # ========== Campos relacionales ==========

    quality_check_ids = fields.One2many(
        'amunet.quality.check',
        'lot_id',
        string='Controles de calidad',
    )

    quality_check_count = fields.Integer(
        string='Controles QC',
        compute='_compute_quality_check_count',
    )

    last_quality_check_id = fields.Many2one(
        'amunet.quality.check',
        string='Último control de calidad',
        compute='_compute_last_quality_check_id',
    )

    can_request_reanalysis = fields.Boolean(
        string='Puede solicitar reanálisis',
        compute='_compute_can_request_reanalysis',
    )

    lot_extension_ids = fields.One2many(
        'amunet.lot.extension',
        'lot_id',
        string='Extensiones de caducidad',
    )

    lot_extension_count = fields.Integer(
        string='Extensiones',
        compute='_compute_lot_extension_count',
    )

    can_extend_expiration = fields.Boolean(
        string='Puede extender caducidad',
        compute='_compute_can_extend_expiration',
    )

    reanalysis_date = fields.Date(
        string='Fecha de reanálisis',
        compute='_compute_reanalysis_date',
        store=True,
        help='Fecha programada para reanálisis: 30 días antes de caducidad',
    )

    # ========== Liberación final DHR ==========

    amunet_lot_release_state = fields.Selection([
        ('pending', 'Pendiente'),
        ('released', 'Liberado'),
    ], string='Estado de liberación DHR', default='pending', readonly=True,
        copy=False, tracking=True)

    amunet_lot_release_quality_check_id = fields.Many2one(
        'amunet.quality.check',
        string='QC de liberación',
        readonly=True,
        copy=False,
        ondelete='restrict',
    )

    amunet_lot_released_by_id = fields.Many2one(
        'res.users',
        string='Liberado por',
        readonly=True,
        copy=False,
    )

    amunet_lot_released_date = fields.Datetime(
        string='Fecha de liberación',
        readonly=True,
        copy=False,
    )

    amunet_lot_release_notes = fields.Text(
        string='Notas de liberación',
        readonly=True,
        copy=False,
    )

    amunet_lot_release_snapshot = fields.Text(
        string='Snapshot DHR',
        readonly=True,
        copy=False,
        help='JSON inmutable con el estado del lote, QC, firmas y movimientos al liberar.',
    )

    amunet_lot_release_hash = fields.Char(
        string='Hash SHA-256 DHR',
        readonly=True,
        copy=False,
        index=True,
    )

    # ========== Computados ==========

    @api.depends('quality_check_ids')
    def _compute_quality_check_count(self):
        for lot in self:
            lot.quality_check_count = len(lot.quality_check_ids)

    @api.depends('quality_check_ids', 'quality_check_ids.state')
    def _compute_last_quality_check_id(self):
        """Retorna el QC completado más reciente del lote (done, pending o awaiting_reception)."""
        for lot in self:
            done_checks = lot.quality_check_ids.filtered(
                lambda c: c.state in ('done', 'pending', 'awaiting_reception')
            ).sorted('id', reverse=True)
            lot.last_quality_check_id = done_checks[0] if done_checks else False

    @api.depends('last_quality_check_id')
    def _compute_can_request_reanalysis(self):
        for lot in self:
            lot.can_request_reanalysis = bool(lot.last_quality_check_id)

    @api.depends('lot_extension_ids')
    def _compute_lot_extension_count(self):
        for lot in self:
            lot.lot_extension_count = len(lot.lot_extension_ids)

    @api.depends('lot_extension_ids.state',
                 'quality_check_ids.state',
                 'quality_check_ids.global_result',
                 'quality_check_ids.analysis_type')
    def _compute_can_extend_expiration(self):
        for lot in self:
            if not lot.expiration_date:
                lot.can_extend_expiration = False
                continue
            # Solo si existe un reanálisis aprobado (análisis tipo reanálisis, finalizado y con resultado APROBADO)
            approved_reanalysis = lot.quality_check_ids.filtered(
                lambda qc: qc.analysis_type == 'reanalysis'
                and qc.state == 'done'
                and qc.global_result == 'pass'
            )
            if not approved_reanalysis:
                lot.can_extend_expiration = False
                continue
            active_ext = lot.lot_extension_ids.filtered(
                lambda e: e.state not in ('done', 'cancelled')
            )
            lot.can_extend_expiration = not bool(active_ext)

    @api.depends('expiration_date')
    def _compute_reanalysis_date(self):
        from dateutil.relativedelta import relativedelta
        for lot in self:
            if lot.expiration_date:
                lot.reanalysis_date = lot.expiration_date - relativedelta(months=1)
                if not lot.removal_date:
                    lot.removal_date = lot.reanalysis_date
            else:
                lot.reanalysis_date = False

    # ========== Liberación final DHR ==========

    def _release_user_ref(self, user):
        if not user:
            return False
        return {
            'id': user.id,
            'name': user.name,
            'login': user.login,
        }

    def _release_record_ref(self, record):
        if not record:
            return False
        return {
            'id': record.id,
            'name': record.display_name,
            'model': record._name,
        }

    def _release_date(self, value):
        return str(value) if value else False

    def _get_lot_release_locked_fields(self):
        return {
            'name',
            'product_id',
            'company_id',
            'factory_lot_id',
            'analysis_number',
            'manufacturing_date',
            'expiration_date',
            'removal_date',
            'use_date',
            'alert_date',
            'amunet_auto_generated',
            'amunet_lot_release_state',
            'amunet_lot_release_quality_check_id',
            'amunet_lot_released_by_id',
            'amunet_lot_released_date',
            'amunet_lot_release_notes',
            'amunet_lot_release_snapshot',
            'amunet_lot_release_hash',
        }

    def _get_lot_release_quality_check(self):
        self.ensure_one()
        checks = self.quality_check_ids.filtered(lambda c: c.active)
        release_checks = checks.filtered(
            lambda c: c.state == 'done' and c.global_result == 'pass'
        ).sorted('id', reverse=True)
        return release_checks[:1]

    def _release_env_model(self, model_name):
        try:
            return self.env[model_name].sudo()
        except KeyError:
            return False

    def _get_lot_release_production(self):
        self.ensure_one()
        Production = self._release_env_model('mrp.production')
        if Production is False:
            return False
        production = Production.search([('lot_producing_ids', 'in', self.id)], limit=1)
        if production:
            return production
        checks = self.quality_check_ids.filtered(lambda c: c.active)
        if checks and 'amunet_production_id' in checks._fields:
            return checks.mapped('amunet_production_id')[:1]
        return Production.browse()

    def _get_lot_release_material_requests(self, production):
        self.ensure_one()
        Request = self._release_env_model('amunet.material.request')
        if Request is False:
            return False
        terms = []
        if self.name:
            terms.append(self.name)
        if production:
            terms.extend(filter(None, [production.name, production.origin]))
        requests = Request.browse()
        for term in list(dict.fromkeys(terms)):
            requests |= Request.search([
                '|',
                ('name', 'ilike', term),
                ('note', 'ilike', term),
            ])
        return requests

    def _get_lot_release_equipment(self, production, release_check):
        Equipment = self._release_env_model('amunet.equipment')
        if Equipment is False:
            return False
        equipment = Equipment.browse()
        if production:
            workcenters = production.workorder_ids.mapped('workcenter_id')
            for workcenter in workcenters:
                if 'amunet_equipment_ids' in workcenter._fields:
                    equipment |= workcenter.amunet_equipment_ids
        if release_check:
            for line in release_check.test_line_ids:
                if 'equipment_id' in line._fields and line.equipment_id:
                    equipment |= line.equipment_id
        return equipment

    def _get_lot_release_training_blockers(self, release_check, equipment):
        enabled = self.env['ir.config_parameter'].sudo().get_param(
            'amunet_competencias.signature_training_check_enabled',
            'False',
        ) == 'True'
        if not enabled or not release_check:
            return []
        Training = self._release_env_model('amunet.registro.capacitacion')
        if Training is False:
            return []

        procedures = self.env['amunet.quality.procedure'].sudo().browse()
        if 'procedure_ids' in release_check._fields:
            procedures |= release_check.procedure_ids.filtered('active')
        for eq in equipment or []:
            if 'procedure_ids' in eq._fields:
                procedures |= eq.procedure_ids.filtered('active')
        if not procedures:
            return []

        signers = (
            release_check.user_realized_id
            | release_check.user_verified_id
            | release_check.user_authorized_id
        ).filtered(lambda user: user and user.active)

        blockers = []
        for user in signers:
            missing = []
            for procedure in procedures:
                training = Training.search([
                    ('user_id', '=', user.id),
                    ('procedure_id', '=', procedure.id),
                    ('state', 'in', ('vigente', 'proxima')),
                ], limit=1)
                if not training:
                    missing.append(procedure.code or procedure.display_name)
            if missing:
                blockers.append(
                    'El firmante %s no tiene capacitacion vigente/proxima en: %s.'
                    % (user.display_name, ', '.join(missing))
                )
        return blockers

    def _get_lot_release_blockers(self):
        self.ensure_one()
        blockers = []

        if self.amunet_lot_release_state == 'released':
            blockers.append('El lote ya está liberado.')
        if not self.product_id:
            blockers.append('El lote no tiene producto asignado.')
        if 'manufacturing_date' in self._fields and not self.manufacturing_date:
            blockers.append('Falta la fecha de fabricación del lote.')

        product_tmpl = self.product_id.product_tmpl_id if self.product_id else False
        if (
            product_tmpl
            and 'use_expiration_date' in product_tmpl._fields
            and product_tmpl.use_expiration_date
            and 'expiration_date' in self._fields
            and not self.expiration_date
        ):
            blockers.append('El producto usa caducidad y el lote no tiene fecha de caducidad.')

        checks = self.quality_check_ids.filtered(lambda c: c.active)
        if not checks:
            blockers.append('No hay controles de calidad vinculados al lote.')
            return blockers

        release_check = self._get_lot_release_quality_check()
        if not release_check:
            blockers.append('No existe un QC aprobado y finalizado para este lote.')
            return blockers

        latest_check = checks.sorted('id', reverse=True)[:1]
        if latest_check and latest_check != release_check:
            blockers.append(
                'El control de calidad más reciente (%s) no está aprobado y finalizado.'
                % latest_check.display_name
            )

        if not release_check.analysis_number:
            blockers.append('El QC de liberación no tiene folio de análisis.')
        if not release_check.user_realized_id:
            blockers.append('Falta la firma "Realizó" en el QC de liberación.')
        if not release_check.user_verified_id:
            blockers.append('Falta la firma "Verificó" en el QC de liberación.')
        if not release_check.user_authorized_id:
            blockers.append('Falta la firma "Autorizó" en el QC de liberación.')

        reception = release_check.final_reception_picking_id
        if reception and reception.state != 'done':
            blockers.append(
                'La recepción final de almacén (%s) todavía no está validada.'
                % reception.display_name
            )

        production = self._get_lot_release_production()
        if production:
            if production.state != 'done':
                blockers.append(
                    'La orden de fabricacion (%s) debe estar cerrada antes de liberar el DHR.'
                    % production.display_name
                )
            open_workorders = production.workorder_ids.filtered(
                lambda wo: wo.state not in ('done', 'cancel')
            )
            if open_workorders:
                blockers.append(
                    'Hay operaciones de manufactura abiertas: %s.'
                    % ', '.join(open_workorders.mapped('display_name')[:5])
                )
            if (
                'amunet_has_supplied_moves' in production._fields
                and production.amunet_has_supplied_moves
                and production.reconciliation_state != 'completed'
            ):
                blockers.append(
                    'La conciliacion de materiales de la MO %s no esta completada.'
                    % production.display_name
                )

        material_requests = self._get_lot_release_material_requests(production)
        if material_requests:
            open_requests = material_requests.filtered(
                lambda req: req.state not in ('closed', 'done', 'cancelled', 'cancel')
            )
            if open_requests:
                blockers.append(
                    'Hay solicitudes de material sin cerrar: %s.'
                    % ', '.join(open_requests.mapped('display_name')[:5])
                )

        equipment = self._get_lot_release_equipment(production, release_check)
        today = fields.Date.today()
        for eq in equipment or []:
            label = eq.serial_number or eq.display_name
            if eq.state != 'active':
                blockers.append('El equipo %s no esta activo.' % label)
            if eq.calibration_required and not eq.next_calibration_date:
                blockers.append('El equipo %s requiere calibracion y no tiene fecha vigente.' % label)
            elif eq.calibration_required and eq.next_calibration_date < today:
                blockers.append(
                    'El equipo %s tiene calibracion vencida (%s).'
                    % (label, eq.next_calibration_date)
                )
            if 'procedure_ids' in eq._fields and not eq.procedure_ids.filtered('active'):
                blockers.append('El equipo %s no tiene PNO aplicable vinculado.' % label)

        blockers.extend(self._get_lot_release_training_blockers(release_check, equipment))

        return blockers

    def _quality_check_snapshot(self, check):
        return {
            'id': check.id,
            'name': check.name,
            'analysis_number': check.analysis_number,
            'analysis_type': check.analysis_type,
            'state': check.state,
            'global_result': check.global_result,
            'product': self._release_record_ref(check.product_id),
            'lot': self._release_record_ref(check.lot_id),
            'picking': self._release_record_ref(check.picking_id),
            'sampling_move': self._release_record_ref(check.sampling_move_id),
            'final_reception': self._release_record_ref(check.final_reception_picking_id),
            'qty_sampling': check.qty_sampling,
            'qty_analyzed': check.qty_analyzed,
            'qty_to_return': check.qty_to_return,
            'original_qty_received': check.original_qty_received,
            'analysis_date': self._release_date(check.analysis_date),
            'signatures': {
                'realized_by': self._release_user_ref(check.user_realized_id),
                'realized_date': self._release_date(check.realized_date),
                'verified_by': self._release_user_ref(check.user_verified_id),
                'verified_date': self._release_date(check.verified_date),
                'authorized_by': self._release_user_ref(check.user_authorized_id),
                'authorized_date': self._release_date(check.authorized_date),
            },
            'test_lines': [{
                'id': line.id,
                'sequence': line.sequence,
                'name': line.name,
                'parameter': self._release_record_ref(line.parameter_id),
                'verdict': line.verdict,
                'result_display': line.result_display,
                'result_notes': line.result_notes,
            } for line in check.test_line_ids.sorted('sequence')],
        }

    def _build_lot_release_snapshot(self, release_check, notes=None):
        self.ensure_one()
        production = self._get_lot_release_production()
        material_requests = self._get_lot_release_material_requests(production)
        equipment = self._get_lot_release_equipment(production, release_check)
        quants = self.env['stock.quant'].search([
            ('lot_id', '=', self.id),
            ('product_id', '=', self.product_id.id),
        ])
        move_lines = self.env['stock.move.line'].search([
            ('lot_id', '=', self.id),
            ('product_id', '=', self.product_id.id),
        ], order='id desc', limit=100)

        return {
            'snapshot_version': '1.1',
            'released_at': self._release_date(fields.Datetime.now()),
            'released_by': self._release_user_ref(self.env.user),
            'release_notes': notes or False,
            'lot': {
                'id': self.id,
                'name': self.name,
                'product': self._release_record_ref(self.product_id),
                'company': self._release_record_ref(self.company_id),
                'factory_lot': self._release_record_ref(self.factory_lot_id),
                'analysis_number': self.analysis_number,
                'manufacturing_date': self._release_date(self.manufacturing_date),
                'expiration_date': self._release_date(self.expiration_date),
                'removal_date': self._release_date(self.removal_date),
            },
            'manufacturing_order': self._release_record_ref(production),
            'material_requests': [
                {
                    'id': request.id,
                    'name': request.display_name,
                    'state': request.state,
                }
                for request in (material_requests or [])
            ],
            'equipment_readiness': [
                {
                    'id': eq.id,
                    'name': eq.display_name,
                    'serial_number': eq.serial_number,
                    'state': eq.state,
                    'calibration_required': eq.calibration_required,
                    'next_calibration_date': self._release_date(eq.next_calibration_date),
                    'procedures': [
                        self._release_record_ref(proc)
                        for proc in eq.procedure_ids.filtered('active')
                    ] if 'procedure_ids' in eq._fields else [],
                }
                for eq in (equipment or [])
            ],
            'release_quality_check': self._quality_check_snapshot(release_check),
            'all_quality_checks': [
                self._quality_check_snapshot(check)
                for check in self.quality_check_ids.filtered(lambda c: c.active).sorted('id')
            ],
            'stock_quants': [{
                'id': quant.id,
                'location': self._release_record_ref(quant.location_id),
                'location_usage': quant.location_id.usage,
                'quantity': quant.quantity,
                'reserved_quantity': getattr(quant, 'reserved_quantity', 0.0),
            } for quant in quants.sorted(lambda q: q.location_id.display_name)],
            'stock_move_lines': [{
                'id': line.id,
                'picking': self._release_record_ref(line.picking_id),
                'move': self._release_record_ref(line.move_id),
                'date': self._release_date(getattr(line, 'date', False)),
                'state': getattr(line, 'state', False),
                'quantity': line.quantity,
                'uom': self._release_record_ref(line.product_uom_id),
                'source': self._release_record_ref(line.location_id),
                'destination': self._release_record_ref(line.location_dest_id),
            } for line in move_lines],
        }

    def _log_lot_release_event(self, success=True, message=None, old_value=None, new_value=None):
        self.ensure_one()
        status = 'EXITOSA' if success else 'FALLIDA'
        self.env['amunet.quality.audit.log'].sudo().create({
            'model_name': 'stock.lot',
            'res_id': self.id,
            'res_name': self.display_name,
            'field_name': 'amunet_lot_release_state',
            'field_description': 'Liberación final DHR',
            'old_value': old_value or self.amunet_lot_release_state or 'pending',
            'new_value': new_value or status,
            'justification': message or 'Firma electrónica de liberación final de lote',
            'user_id': self.env.user.id,
        })

    def action_open_lot_extensions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Extensiones de caducidad — %s' % self.name,
            'res_model': 'amunet.lot.extension',
            'view_mode': 'list,form',
            'domain': [('lot_id', '=', self.id)],
            'context': {'default_lot_id': self.id},
        }

    def action_open_new_extension(self):
        self.ensure_one()
        # Buscar reanálisis aprobado más reciente
        last_check = self.quality_check_ids.filtered(
            lambda c: c.analysis_type == 'reanalysis' and c.state == 'done'
        ).sorted('id', reverse=True)[:1]

        extension = self.env['amunet.lot.extension'].create({
            'lot_id': self.id,
            'months_extended': 0,
            'expiration_date_before': self.expiration_date,
            'reanalysis_check_id': last_check.id if last_check else False,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Extensión de caducidad',
            'res_model': 'amunet.lot.extension',
            'res_id': extension.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_lot_release_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Liberar lote',
            'res_model': 'amunet.quality.lot.release.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id,
                'active_model': 'stock.lot',
                'default_lot_id': self.id,
            },
        }

    def _action_release_lot(self, notes=None):
        self.ensure_one()
        blockers = self._get_lot_release_blockers()
        if blockers:
            raise UserError('\n'.join(blockers))

        release_check = self._get_lot_release_quality_check()
        old_state = self.amunet_lot_release_state or 'pending'
        snapshot = self._build_lot_release_snapshot(release_check, notes=notes)
        snapshot_text = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, indent=2, default=str)
        snapshot_hash = hashlib.sha256(snapshot_text.encode('utf-8')).hexdigest()

        self.with_context(skip_lot_release_lock=True).write({
            'amunet_lot_release_state': 'released',
            'amunet_lot_release_quality_check_id': release_check.id,
            'amunet_lot_released_by_id': self.env.user.id,
            'amunet_lot_released_date': fields.Datetime.now(),
            'amunet_lot_release_notes': notes or False,
            'amunet_lot_release_snapshot': snapshot_text,
            'amunet_lot_release_hash': snapshot_hash,
        })
        self._log_lot_release_event(
            success=True,
            old_value=old_state,
            new_value='released:%s' % snapshot_hash,
            message='Liberación final de lote con snapshot DHR inmutable',
        )

        if hasattr(self, 'message_post'):
            self.message_post(
                body=Markup(
                    'Lote liberado con firma electrónica.<br/>'
                    'QC: <b>%s</b><br/>'
                    'Hash DHR: <code>%s</code>'
                    % (release_check.display_name, snapshot_hash)
                ),
                message_type='notification',
            )
        return True

    # ========== Acciones ==========

    def action_view_quality_checks(self):
        """Abre la lista de controles de calidad asociados a este lote."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Controles de calidad — {self.name}',
            'res_model': 'amunet.quality.check',
            'view_mode': 'list,form',
            'domain': [('lot_id', '=', self.id)],
            'context': {'default_lot_id': self.id},
        }

    def action_request_reanalysis(self):
        """
        Abre el wizard de reanálisis desde Inventario.

        Busca el control de calidad completado más reciente del lote y abre
        el wizard preconfigurado con ese análisis. Si no existe ningún análisis
        completado, muestra un mensaje de error al usuario.
        """
        self.ensure_one()
        if not self.last_quality_check_id:
            raise UserError(
                'No existe ningún análisis de calidad completado para el lote "%s".\n\n'
                'Solo es posible solicitar un reanálisis de lotes que ya pasaron '
                'por Control de Calidad (estado: En revisión o Finalizado).' % self.name
            )
        return {
            'type': 'ir.actions.act_window',
            'name': 'Solicitar reanálisis',
            'res_model': 'amunet.quality.reanalysis.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.last_quality_check_id.id,
                'active_model': 'amunet.quality.check',
                'origin_model': 'stock.lot',
                'origin_lot_id': self.id,
            },
        }

    def write(self, vals):
        locked_fields = self._get_lot_release_locked_fields().intersection(vals.keys())
        if locked_fields and not self.env.context.get('skip_lot_release_lock'):
            locked_records = self.filtered(lambda lot: lot.amunet_lot_release_state == 'released')
            if locked_records:
                raise UserError(
                    'No se pueden modificar campos críticos de un lote liberado. '
                    'Cree un reanálisis o registre una desviación/CAPA si necesita cambiar el expediente.'
                )
        return super().write(vals)

    # ========== Alerta automática de reanálisis ==========

    @api.model
    def _cron_alerta_reanalisis_caducidad(self):
        """
        Cron diario: detecta lotes que llegan hoy a su fecha de reanálisis
        (caducidad − 30 días) y envía alerta al equipo de Calidad.
        Solo aplica a materiales donde la categoría tiene meses de extensión > 0.
        No genera alerta si ya existe un reanálisis activo para ese lote.
        """
        from datetime import date
        hoy = date.today()

        lotes = self.search([
            ('reanalysis_date', '=', hoy),
            ('product_id.categ_id.reanalysis_extension_months', '>', 0),
        ])

        if not lotes:
            return

        # Filtrar los que NO tienen ya un reanálisis en curso
        lotes_pendientes = lotes.filtered(lambda lot: not lot.quality_check_ids.filtered(
            lambda qc: qc.analysis_type == 'reanalysis' and qc.state not in ('done', 'cancel')
        ))

        if not lotes_pendientes:
            return

        # Grupo de calidad para notificar
        grupo_calidad = self.env.ref('amunet_quality.group_quality_analyst', raise_if_not_found=False)
        usuarios_calidad = grupo_calidad.users if grupo_calidad else self.env['res.users'].search([
            ('login', 'in', ['s.controldecalidad@amunet.com.mx',
                             'analista1cc@amunet.com.mx',
                             'analista2cc@amunet.com.mx'])
        ])

        # Crear actividad en cada lote y preparar cuerpo del correo
        lineas_correo = []
        tipo_actividad = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)

        for lot in lotes_pendientes:
            meses = lot.product_id.product_tmpl_id.effective_reanalysis_months
            lineas_correo.append(
                f'• {lot.product_id.display_name} — Lote: {lot.name} '
                f'| Caduca: {lot.expiration_date} '
                f'| Extensión posible: {meses} mes(es)'
            )
            # Actividad en el lote para los analistas
            for usuario in usuarios_calidad:
                lot.activity_schedule(
                    activity_type_id=tipo_actividad.id if tipo_actividad else False,
                    summary='Reanálisis por caducidad próxima',
                    note=(
                        f'El lote <b>{lot.name}</b> de <b>{lot.product_id.display_name}</b> '
                        f'llega hoy a su fecha de reanálisis.<br/>'
                        f'Caducidad: <b>{lot.expiration_date}</b><br/>'
                        f'Si el reanálisis aprueba, se puede extender <b>{meses} mes(es)</b>.'
                    ),
                    user_id=usuario.id,
                    date_deadline=hoy,
                )

        # Enviar correo al equipo de Calidad
        if lineas_correo and usuarios_calidad:
            cuerpo = (
                '<p>Buenos días,</p>'
                '<p>Los siguientes lotes llegaron hoy a su <b>fecha de reanálisis</b> '
                '(30 días antes de caducar). Por favor programa el reanálisis correspondiente:</p>'
                '<ul>' +
                ''.join(f'<li>{l}</li>' for l in lineas_correo) +
                '</ul>'
                '<p>Puedes iniciar el reanálisis desde el lote en '
                '<a href="/odoo/inventory/products/lots">Inventario → Lotes</a>.</p>'
                '<p>— Sistema de Calidad Amunet</p>'
            )
            for usuario in usuarios_calidad:
                if usuario.email:
                    self.env['mail.mail'].sudo().create({
                        'subject': f'[Calidad] {len(lotes_pendientes)} lote(s) requieren reanálisis hoy ({hoy})',
                        'email_to': usuario.email,
                        'body_html': cuerpo,
                        'auto_delete': True,
                    }).send()
