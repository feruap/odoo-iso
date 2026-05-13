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
        quants = self.env['stock.quant'].search([
            ('lot_id', '=', self.id),
            ('product_id', '=', self.product_id.id),
        ])
        move_lines = self.env['stock.move.line'].search([
            ('lot_id', '=', self.id),
            ('product_id', '=', self.product_id.id),
        ], order='id desc', limit=100)

        return {
            'snapshot_version': '1.0',
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
