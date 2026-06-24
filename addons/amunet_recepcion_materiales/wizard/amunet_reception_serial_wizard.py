# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AmunetReceptionSerialWizard(models.TransientModel):
    _name = 'amunet.reception.serial.wizard'
    _description = 'Captura de números de serie en recepción'

    picking_id = fields.Many2one('stock.picking', required=True)
    line_ids = fields.One2many(
        'amunet.reception.serial.wizard.line', 'wizard_id', string='Seriales')
    lot_count = fields.Integer(compute='_compute_lot_count')

    @api.depends('picking_id')
    def _compute_lot_count(self):
        for wiz in self:
            lots = wiz.picking_id.move_line_ids.lot_id.filtered('amunet_allow_multi_serial')
            wiz.lot_count = len(lots)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        picking_id = res.get('picking_id') or self.env.context.get('default_picking_id')
        if picking_id and 'line_ids' in fields_list:
            picking = self.env['stock.picking'].browse(picking_id)
            lots = picking.move_line_ids.lot_id.filtered('amunet_allow_multi_serial')
            lines = []
            for lot in lots:
                # Cargar seriales existentes
                for serial in lot.amunet_serial_ids.sorted('serial_number'):
                    lines.append((0, 0, {
                        'lot_id': lot.id,
                        'serial_id': serial.id,
                        'serial_number': serial.serial_number,
                        'notes': serial.notes,
                    }))
                # Si no tiene seriales, agregar una línea vacía para facilitar captura
                if not lot.amunet_serial_ids:
                    lines.append((0, 0, {'lot_id': lot.id}))
            res['line_ids'] = lines
        return res

    def action_save(self):
        # Ignorar líneas completamente vacías (sin serial ni lote) — el usuario las
        # deja cuando hace clic en "Añadir una línea" pero no escribe nada.
        active_lines = self.line_ids.filtered(
            lambda l: l.serial_number or l.lot_id
        )
        if not active_lines:
            raise UserError(_('Agrega al menos un número de serie antes de guardar.'))

        # Si alguna línea tiene serial pero no lote, intentamos asignar el único
        # lote de la recepción (caso más común: un solo equipo recibido).
        lines_sin_lote = active_lines.filtered(lambda l: l.serial_number and not l.lot_id)
        if lines_sin_lote:
            picking = self.picking_id
            lots_equipo = picking.move_line_ids.lot_id.filtered('amunet_allow_multi_serial')
            if len(lots_equipo) == 1:
                lines_sin_lote.write({'lot_id': lots_equipo.id})
            else:
                raise UserError(_(
                    'Hay líneas sin lote asignado y la recepción tiene más de un '
                    'equipo. Recarga el wizard para que se asignen automáticamente.'
                ))

        if any(not l.serial_number for l in active_lines):
            raise UserError(_('Hay líneas sin número de serie. Complétalas o elimínalas.'))

        # Agrupar líneas por lote
        lots_procesados = {}
        for line in active_lines:
            lots_procesados.setdefault(line.lot_id, []).append(line)

        Serial = self.env['amunet.equipment.serial'].sudo()
        for lot, lines in lots_procesados.items():
            # IDs de seriales que vienen del wizard (los que ya existían)
            serial_ids_en_wizard = {l.serial_id.id for l in lines if l.serial_id}
            # Borrar los que se eliminaron del wizard
            to_delete = lot.amunet_serial_ids.filtered(
                lambda s: s.id not in serial_ids_en_wizard)
            to_delete.unlink()
            # Actualizar existentes y crear nuevos
            for line in lines:
                if line.serial_id:
                    line.serial_id.write({
                        'serial_number': line.serial_number,
                        'notes': line.notes,
                    })
                else:
                    Serial.create({
                        'lot_id': lot.id,
                        'serial_number': line.serial_number,
                        'notes': line.notes or False,
                    })

        return {'type': 'ir.actions.act_window_close'}


class AmunetReceptionSerialWizardLine(models.TransientModel):
    _name = 'amunet.reception.serial.wizard.line'
    _description = 'Línea de serial en recepción'
    _order = 'lot_id, serial_number'

    wizard_id = fields.Many2one(
        'amunet.reception.serial.wizard', required=True, ondelete='cascade')
    lot_id = fields.Many2one('stock.lot', string='Lote')
    lot_name = fields.Char(related='lot_id.name', string='Lote', readonly=True)
    serial_id = fields.Many2one(
        'amunet.equipment.serial', string='Serial existente')
    serial_number = fields.Char(string='Número de serie')
    notes = fields.Text(string='Notas')
