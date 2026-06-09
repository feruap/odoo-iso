# -*- coding: utf-8 -*-
import pytz
from datetime import datetime, time as dt_time
from dateutil.relativedelta import relativedelta
from odoo import models, fields

RECEPTION_FIELDS = {'amunet_mfg_date', 'amunet_exp_date', 'amunet_supplier_lot'}


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


class StockMove(models.Model):
    _inherit = 'stock.move'

    amunet_supplier_lot = fields.Char('Lote del proveedor')
    amunet_mfg_date = fields.Date('Fecha de fabricación')
    amunet_exp_date = fields.Date('Fecha de caducidad')

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
            if 'amunet_mfg_date' in vals:
                line_vals['manufacturing_date'] = move.amunet_mfg_date
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
                vals['manufacturing_date'] = move.amunet_mfg_date
            if move.amunet_exp_date:
                vals['expiration_date'] = _date_to_local_9am(move.amunet_exp_date, move.env)
                vals['removal_date'] = _calc_removal_date(move.amunet_exp_date, move.env)
            move.move_line_ids.write(vals)
        return super()._action_done(cancel_backorder=cancel_backorder)
