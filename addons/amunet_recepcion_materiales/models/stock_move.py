# -*- coding: utf-8 -*-
import pytz
from datetime import datetime, time as dt_time
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api

RECEPTION_FIELDS = {'amunet_mfg_date', 'amunet_exp_date', 'amunet_supplier_lot'}
LINE_TRIGGER = {'amunet_supplier_lot', 'amunet_mfg_date', 'expiration_date'}


def _date_to_local_9am(date_val, env):
    """Convierte una fecha a las 9:00 AM en la zona horaria de la empresa, expresado en UTC."""
    tz_name = env.company.partner_id.tz or 'America/Mexico_City'
    tz = pytz.timezone(tz_name)
    local_dt = tz.localize(datetime.combine(date_val, dt_time(9, 0, 0)))
    return local_dt.astimezone(pytz.UTC).replace(tzinfo=None)


def _calc_removal_date(exp_date, env):
    """Calcula fecha de remoción: 2 meses antes de caducidad. Si cae en pasado, igual a caducidad."""
    calculated = exp_date - relativedelta(months=2)
    today = fields.Date.context_today(env.user)
    calc_date = calculated.date() if hasattr(calculated, 'date') else calculated
    if calc_date < today:
        return _date_to_local_9am(exp_date, env)
    return _date_to_local_9am(calculated, env)


def _parse_mfg_date(val):
    """Intenta parsear una fecha de fabricación en texto. Devuelve date o None."""
    clean = val.strip().upper()
    if clean == 'NA':
        return None
    for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(clean, fmt).date()
        except ValueError:
            continue
    return None


class StockMove(models.Model):
    _inherit = 'stock.move'

    amunet_supplier_lot = fields.Char('Lote del proveedor')
    amunet_mfg_date = fields.Char('Fecha de fabricación')
    amunet_exp_date = fields.Date('Fecha de caducidad')
    amunet_removal_date = fields.Datetime(
        compute='_compute_amunet_removal_date',
        string='Fecha de remoción',
        store=False,
    )
    amunet_is_equipment = fields.Boolean(
        related='product_id.product_tmpl_id.amunet_allow_multi_serial',
        string='Es equipo',
        store=False,
    )


    def _compute_amunet_removal_date(self):
        for move in self:
            if move.amunet_exp_date:
                move.amunet_removal_date = _calc_removal_date(move.amunet_exp_date, move.env)
            else:
                move.amunet_removal_date = False

    def write(self, vals):
        res = super().write(vals)
        if not (RECEPTION_FIELDS & set(vals)):
            return res
        for move in self.filtered(
            lambda m: m.picking_type_id.code == 'incoming' and m.move_line_ids
        ):
            line_vals = {}
            if 'amunet_supplier_lot' in vals and move.amunet_supplier_lot:
                factory_lot = move.env['amunet.lot.factory'].sudo().search(
                    [('name', '=', move.amunet_supplier_lot)], limit=1
                )
                if not factory_lot:
                    factory_lot = move.env['amunet.lot.factory'].sudo().create(
                        {'name': move.amunet_supplier_lot}
                    )
                line_vals['factory_lot_id'] = factory_lot.id
            if 'amunet_mfg_date' in vals and move.amunet_mfg_date:
                mfg = _parse_mfg_date(move.amunet_mfg_date)
                if mfg:
                    line_vals['manufacturing_date'] = mfg
            if 'amunet_exp_date' in vals and move.amunet_exp_date:
                line_vals['expiration_date'] = _date_to_local_9am(move.amunet_exp_date, move.env)
                line_vals['removal_date'] = _calc_removal_date(move.amunet_exp_date, move.env)
            if line_vals:
                move.move_line_ids.write(line_vals)
        return res

    def _action_done(self, cancel_backorder=False):
        for move in self.filtered(
            lambda m: m.picking_type_id.code == 'incoming' and m.move_line_ids
            and (m.amunet_supplier_lot or m.amunet_mfg_date or m.amunet_exp_date)
        ):
            vals = {}
            if move.amunet_supplier_lot:
                factory_lot = self.env['amunet.lot.factory'].sudo().search(
                    [('name', '=', move.amunet_supplier_lot)], limit=1
                )
                if not factory_lot:
                    factory_lot = self.env['amunet.lot.factory'].sudo().create(
                        {'name': move.amunet_supplier_lot}
                    )
                vals['factory_lot_id'] = factory_lot.id
            if move.amunet_mfg_date:
                mfg = _parse_mfg_date(move.amunet_mfg_date)
                if mfg:
                    vals['manufacturing_date'] = mfg
            if move.amunet_exp_date:
                vals['expiration_date'] = _date_to_local_9am(move.amunet_exp_date, move.env)
                vals['removal_date'] = _calc_removal_date(move.amunet_exp_date, move.env)
            move.move_line_ids.write(vals)
        return super()._action_done(cancel_backorder=cancel_backorder)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    amunet_supplier_lot = fields.Char('Lote del proveedor')
    amunet_mfg_date = fields.Char('Fecha fab. (texto)')

    amunet_calidad_estado = fields.Selection([
        ('quarantine', 'En cuarentena'),
        ('in_review', 'En revisión'),
        ('released', 'Liberado'),
    ], string='Estado en Calidad', compute='_compute_amunet_calidad_estado')

    @api.depends('lot_id', 'lot_id.amunet_lot_release_state')
    def _compute_amunet_calidad_estado(self):
        for line in self:
            lot = line.lot_id
            if not lot:
                line.amunet_calidad_estado = False
                continue
            if lot.amunet_lot_release_state == 'released':
                line.amunet_calidad_estado = 'released'
            else:
                qc_activo = self.env['amunet.quality.check'].search([
                    ('lot_id', '=', lot.id),
                    ('state', 'in', ('in_progress', 'pending', 'awaiting_reception')),
                ], limit=1)
                line.amunet_calidad_estado = 'in_review' if qc_activo else 'quarantine'

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get('_amunet_line_no_propagate'):
            return res
        if not (LINE_TRIGGER & set(vals)):
            return res
        for line in self.filtered(lambda l: l.picking_id.picking_type_id.code == 'incoming'):
            extra = {}
            if 'amunet_supplier_lot' in vals and line.amunet_supplier_lot:
                factory_lot = line.env['amunet.lot.factory'].sudo().search(
                    [('name', '=', line.amunet_supplier_lot)], limit=1
                )
                if not factory_lot:
                    factory_lot = line.env['amunet.lot.factory'].sudo().create(
                        {'name': line.amunet_supplier_lot}
                    )
                extra['factory_lot_id'] = factory_lot.id
            if 'amunet_mfg_date' in vals and line.amunet_mfg_date:
                mfg = _parse_mfg_date(line.amunet_mfg_date)
                if mfg:
                    extra['manufacturing_date'] = mfg
            if 'expiration_date' in vals and line.expiration_date:
                exp_date = line.expiration_date.date() if hasattr(line.expiration_date, 'date') else line.expiration_date
                extra['removal_date'] = _calc_removal_date(exp_date, line.env)
            if extra:
                line.with_context(_amunet_line_no_propagate=True).write(extra)
        return res
