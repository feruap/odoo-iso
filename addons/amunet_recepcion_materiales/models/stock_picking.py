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

    # ── action_confirm: asignar destino automático + corregir lote ──────────
    def action_confirm(self):
        for picking in self.filtered(lambda p: p.picking_type_code == 'incoming'):
            qc_loc = picking._get_quarantine_location()
            if not qc_loc:
                continue
            for move in picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
                if move.product_id.product_tmpl_id.amunet_requires_quarantine:
                    move.location_dest_id = qc_loc.id

        result = super().action_confirm()

        # amunet_lot genera lot_name en la línea pero no crea el registro stock.lot
        # hasta la validación. Lo creamos aquí para que sea visible en la tabla.
        for picking in self.filtered(lambda p: p.picking_type_code == 'incoming'):
            for line in picking.move_line_ids.filtered(lambda l: l.lot_name and not l.lot_id):
                lot = self.env['stock.lot'].search([
                    ('name', '=', line.lot_name),
                    ('product_id', '=', line.product_id.id),
                ], limit=1)
                if not lot:
                    lot = self.env['stock.lot'].sudo().create({
                        'name': line.lot_name,
                        'product_id': line.product_id.id,
                        'company_id': line.company_id.id,
                    })
                line.lot_id = lot.id

        return result

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

    def _action_done(self):
        res = super()._action_done()
        for picking in self.filtered(
            lambda p: p.picking_type_code == 'incoming' and p.amunet_con_observaciones
        ):
            criterios = {
                'Empaque íntegro': picking.amunet_crit1,
                'Etiqueta legible': picking.amunet_crit2,
                'Sin daños visibles': picking.amunet_crit3,
                'Certificado de análisis': picking.amunet_crit4,
                'Cantidad correcta': picking.amunet_crit5,
            }
            fallidos = [nombre for nombre, val in criterios.items() if val == 'nok']
            if not fallidos:
                continue
            detalle = ', '.join(fallidos)
            obs = picking.amunet_crit_obs or '(sin observaciones adicionales)'
            msg = (
                f'⚠️ <b>Material recibido con observaciones — requiere revisión de Calidad</b><br/>'
                f'Criterios que no cumplen: <b>{detalle}</b><br/>'
                f'Observaciones: {obs}<br/>'
                f'Recepción: {picking.name} | Recibió: {picking.amunet_receptor_id.name or "—"}'
            )
            lot_ids = picking.move_line_ids.mapped('lot_id').filtered(lambda l: l.id)
            qcs = self.env['amunet.quality.check'].search([
                ('lot_id', 'in', lot_ids.ids),
                ('state', 'not in', ('done',)),
            ])
            for qc in qcs:
                qc.message_post(body=msg, message_type='notification',
                                subtype_xmlid='mail.mt_note')
        return res
