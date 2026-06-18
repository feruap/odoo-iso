# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError

CRITERIO_SEL = [('ok', 'Cumple'), ('nok', 'No cumple')]
CRITERIO_SEL_NA = [('ok', 'Cumple'), ('nok', 'No cumple'), ('na', 'N/A')]


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # ── Criterios de aceptación ─────────────────────────────────────────────
    amunet_crit1 = fields.Selection(CRITERIO_SEL, 'Empaque íntegro, sin perforaciones ni daños externos')
    amunet_crit2 = fields.Selection(CRITERIO_SEL, 'Etiqueta legible con información correcta (producto, lote, fechas)')
    amunet_crit3 = fields.Selection(CRITERIO_SEL, 'Sin daños visibles en el material (deformaciones, humedad, etc.)')
    amunet_crit4 = fields.Selection(CRITERIO_SEL_NA, 'Certificado de análisis del proveedor recibido y correcto')
    amunet_crit5 = fields.Selection(CRITERIO_SEL, 'Cantidad recibida coincide con lo solicitado en la orden')
    amunet_crit_obs = fields.Text('Observaciones de inspección')

    # ── Disposición ──────────────────────────────────────────────────────────
    amunet_con_observaciones = fields.Boolean(
        'Con observaciones — requiere revisión de Calidad',
        help='Marca esto si algo llegó en mal estado o con discrepancias. '
             'Quedará registrado y se notificará a Calidad.',
    )

    # ── Firma ────────────────────────────────────────────────────────────────
    amunet_receptor_id = fields.Many2one(
        'res.users', 'Recibió',
        help='Usuario que inspeccionó y validó esta recepción.',
    )

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _get_quarantine_location(self):
        """Ubicación de Control de calidad del almacén de este picking."""
        wh = self.picking_type_id.warehouse_id
        if not wh:
            return self.env['stock.location']
        parent = wh.lot_stock_id.location_id
        return self.env['stock.location'].search([
            ('location_id', '=', parent.id),
            ('usage', '=', 'internal'),
            ('name', 'ilike', 'calidad'),
        ], limit=1)

    # ── Onchange: auto-marcar "con observaciones" si algún criterio falla ──
    @api.onchange('amunet_crit1', 'amunet_crit2', 'amunet_crit3',
                  'amunet_crit4', 'amunet_crit5')
    def _onchange_criterios(self):
        if any(getattr(self, f'amunet_crit{i}') == 'nok' for i in range(1, 6)):
            self.amunet_con_observaciones = True

    # ── action_confirm: asignar destino por producto + generar lotes ────────
    def action_confirm(self):
        for picking in self.filtered(lambda p: p.picking_type_code == 'incoming'):
            qc_loc = picking._get_quarantine_location()
            for move in picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
                # Destino automático según configuración del producto
                if qc_loc and move.product_id.product_tmpl_id.amunet_requires_quarantine:
                    move.location_dest_id = qc_loc.id
                # Generar lote Amunet si aplica
                if (move.product_id.tracking in ('lot', 'serial')
                        and move.product_id.lot_sequence_id
                        and not move.lot_ids):
                    lot_name = move.product_id.lot_sequence_id.next_by_id()
                    lot = self.env['stock.lot'].search([
                        ('name', '=', lot_name),
                        ('product_id', '=', move.product_id.id),
                    ], limit=1)
                    if not lot:
                        lot = self.env['stock.lot'].sudo().create({
                            'name': lot_name,
                            'product_id': move.product_id.id,
                            'company_id': move.company_id.id,
                        })
                    move.lot_ids = [(4, lot.id)]
        return super().action_confirm()

    # ── button_validate: pedir PIN antes de validar ──────────────────────────
    def button_validate(self):
        if self.env.context.get('_skip_pin_wizard'):
            return super().button_validate()
        incoming = self.filtered(lambda p: p.picking_type_code == 'incoming'
                                 and p.state not in ('done', 'cancel'))
        if not incoming:
            return super().button_validate()
        # Advertir si algún criterio no fue llenado
        unfilled = incoming.filtered(
            lambda p: not all([p.amunet_crit1, p.amunet_crit2,
                               p.amunet_crit3, p.amunet_crit4, p.amunet_crit5])
        )
        if unfilled:
            raise UserError(_(
                'Faltan criterios de aceptación por revisar en la pestaña '
                '"Inspección de entrada". Completa todos los criterios antes de validar.'
            ))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirmar recepción',
            'res_model': 'amunet.recepcion.pin.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_picking_id': self.id},
        }
