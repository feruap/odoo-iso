# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AmunetLotSerialSplitWizard(models.TransientModel):
    _name = 'amunet.lot.serial.split.wizard'
    _description = 'Separar seriales defectuosos a nuevo lote'

    lot_id = fields.Many2one('stock.lot', string='Lote origen', required=True)
    product_id = fields.Many2one(related='lot_id.product_id', readonly=True)
    line_ids = fields.One2many(
        'amunet.lot.serial.split.line', 'wizard_id', string='Seriales')
    new_lot_name = fields.Char(
        compute='_compute_new_lot_name', string='Nombre del lote de rechazados')
    defective_count = fields.Integer(
        compute='_compute_defective_count', string='Seleccionados')

    @api.depends('lot_id')
    def _compute_new_lot_name(self):
        for wiz in self:
            if not wiz.lot_id:
                wiz.new_lot_name = False
                continue
            name = wiz.lot_id.name
            try:
                prefix = name[:-2]
                seq = int(name[-2:])
            except (ValueError, IndexError):
                wiz.new_lot_name = name + '_R'
                continue
            # Busca el siguiente número disponible
            for _ in range(98):
                seq += 1
                candidate = prefix + str(seq).zfill(2)
                exists = self.env['stock.lot'].search([
                    ('name', '=', candidate),
                    ('product_id', '=', wiz.lot_id.product_id.id),
                ], limit=1)
                if not exists:
                    wiz.new_lot_name = candidate
                    break
            else:
                wiz.new_lot_name = name + '_R'

    @api.depends('line_ids.is_defective')
    def _compute_defective_count(self):
        for wiz in self:
            wiz.defective_count = len(wiz.line_ids.filtered('is_defective'))

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        lot_id = res.get('lot_id')
        if lot_id and 'line_ids' in fields_list:
            lot = self.env['stock.lot'].browse(lot_id)
            res['line_ids'] = [(0, 0, {
                'serial_id': s.id,
                'is_defective': False,
            }) for s in lot.amunet_serial_ids.sorted('serial_number')]
        return res

    def action_split(self):
        defective_lines = self.line_ids.filtered('is_defective')
        if not defective_lines:
            raise UserError(_('Selecciona al menos un serial defectuoso antes de separar.'))

        # El lote origen es siempre el lote raíz (no el padre inmediato si ya es derivado)
        source = self.lot_id.amunet_source_lot_id or self.lot_id
        # sudo() para que Calidad pueda confirmar sin necesitar permisos de escritura
        # en stock.lot ni en amunet.equipment.serial
        new_lot = self.env['stock.lot'].sudo().create({
            'name': self.new_lot_name,
            'product_id': self.lot_id.product_id.id,
            'company_id': self.lot_id.company_id.id,
            'amunet_source_lot_id': source.id,
        })

        n = len(defective_lines)
        defective_lines.mapped('serial_id').sudo().write({'lot_id': new_lot.id})

        # Mueve las unidades en stock (1 unidad por serial defectuoso)
        quants_01 = self.env['stock.quant'].sudo().search([
            ('lot_id', '=', self.lot_id.id),
            ('location_id.usage', '=', 'internal'),
            ('quantity', '>', 0),
        ])
        moved = 0
        for quant in quants_01:
            to_move = min(n - moved, int(quant.quantity))
            if to_move <= 0:
                continue
            self.env['stock.quant'].sudo()._update_available_quantity(
                quant.product_id, quant.location_id, -to_move, lot_id=self.lot_id)
            self.env['stock.quant'].sudo()._update_available_quantity(
                quant.product_id, quant.location_id, to_move, lot_id=new_lot)
            moved += to_move
            if moved >= n:
                break

        serial_list = ', '.join(defective_lines.mapped('serial_id.serial_number'))
        self.lot_id.message_post(
            body=(f'<b>Separación de seriales defectuosos</b><br/>'
                  f'{n} serial(es) movido(s) al lote <b>{new_lot.name}</b>: {serial_list}'),
            message_type='notification', subtype_xmlid='mail.mt_note',
        )
        new_lot.message_post(
            body=(f'<b>Lote creado por separación de rechazados</b><br/>'
                  f'Origen: <b>{self.lot_id.name}</b><br/>'
                  f'Seriales: {serial_list}'),
            message_type='notification', subtype_xmlid='mail.mt_note',
        )

        return {
            'type': 'ir.actions.act_window',
            'name': _('Lote de rechazados creado'),
            'res_model': 'stock.lot',
            'res_id': new_lot.id,
            'view_mode': 'form',
            'target': 'current',
        }


class AmunetLotSerialSplitLine(models.TransientModel):
    _name = 'amunet.lot.serial.split.line'
    _description = 'Línea del asistente de separación de seriales'
    _order = 'serial_number'

    wizard_id = fields.Many2one(
        'amunet.lot.serial.split.wizard', required=True, ondelete='cascade')
    serial_id = fields.Many2one(
        'amunet.equipment.serial', string='Serial', required=True)
    serial_number = fields.Char(
        related='serial_id.serial_number', string='Número de serie', readonly=True)
    notes = fields.Text(
        related='serial_id.notes', string='Notas', readonly=True)
    is_defective = fields.Boolean(string='Defectuoso', default=False)
