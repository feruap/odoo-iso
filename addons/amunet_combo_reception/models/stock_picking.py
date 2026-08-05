# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # ── Ubicaciones / tipo de operacion (get-or-create, sin data.xml) ──────
    @api.model
    def _amunet_combo_warehouse(self):
        """Almacen donde se reciben los combos (MP Fabrica / AMP), o el 1o."""
        WH = self.env['stock.warehouse']
        wh = WH.search([('code', '=', 'AMP')], limit=1) or \
            WH.search([('name', 'ilike', 'Materia Prima F')], limit=1) or \
            WH.search([], limit=1)
        return wh

    @api.model
    def _amunet_combo_virtual_location(self):
        """Ubicacion virtual de conversion (por donde pasa el combo al
        convertirse en sus hojas). Uso 'inventory' para no afectar valuacion."""
        Loc = self.env['stock.location']
        loc = Loc.search([('name', '=', 'Conversión de combos'),
                          ('usage', '=', 'inventory')], limit=1)
        if not loc:
            loc = Loc.create({
                'name': 'Conversión de combos', 'usage': 'inventory'})
        return loc

    @api.model
    def _amunet_combo_conversion_type(self):
        """Tipo de operacion interno 'Conversión de combos' (existencias)."""
        PT = self.env['stock.picking.type']
        pt = PT.search([('name', '=', 'Conversión de combos'),
                        ('code', '=', 'internal')], limit=1)
        if not pt:
            wh = self._amunet_combo_warehouse()
            seq = self.env['ir.sequence'].create({
                'name': 'Conversión de combos', 'prefix': 'CONV/',
                'padding': 5, 'company_id': wh.company_id.id})
            pt = PT.create({
                'name': 'Conversión de combos', 'code': 'internal',
                'sequence_code': 'CONV', 'sequence_id': seq.id,
                'warehouse_id': wh.id,
                'default_location_src_id': wh.lot_stock_id.id,
                'default_location_dest_id': wh.lot_stock_id.id})
        return pt

    @api.model
    def _amunet_combo_input_location(self):
        """Ubicacion de ENTRADA del almacen (AMP/Entrada): ahi aterriza el
        combo al recibirlo, como el resto del material recibido — NO en
        Existencias (que es stock ya liberado). De la Entrada se convierte."""
        wh = self._amunet_combo_warehouse()
        return wh.wh_input_stock_loc_id or wh.lot_stock_id

    # ── Ruteo: el combo se recibe en ENTRADA (no en Existencias) ────────────
    def action_confirm(self):
        res = super().action_confirm()
        # amunet_recepcion rutea la MP sin cuarentena directo a Existencias; el
        # combo debe quedar en la ENTRADA del almacen (como cualquier material
        # recibido) y de ahi se dispara la conversion.
        input_loc = self._amunet_combo_input_location()
        if input_loc:
            for picking in self.filtered(
                    lambda p: p.picking_type_code == 'incoming'):
                combo_moves = picking.move_ids.filtered(
                    lambda m: m.state not in ('done', 'cancel')
                    and m.product_id.product_tmpl_id.es_combo_compra
                    and m.location_dest_id != input_loc)
                for m in combo_moves:
                    m.location_dest_id = input_loc.id
                    m.move_line_ids.write({'location_dest_id': input_loc.id})
        return res

    # ── Al llegar el combo a ENTRADA, generar el 2o ingreso (conversion) ────
    def _action_done(self):
        res = super()._action_done()
        conv_pt = self.env['stock.picking.type'].search(
            [('name', '=', 'Conversión de combos'), ('code', '=', 'internal')],
            limit=1)
        input_loc = self._amunet_combo_input_location()
        for picking in self:
            # no re-disparar sobre la propia conversion
            if conv_pt and picking.picking_type_id == conv_pt:
                continue
            # combos que acaban de aterrizar en la ENTRADA del almacen
            combo_moves = picking.move_ids.filtered(
                lambda m: m.state == 'done'
                and m.product_id.product_tmpl_id.es_combo_compra
                and m.location_dest_id == input_loc)
            if combo_moves:
                picking._amunet_create_combo_conversion(combo_moves, input_loc)
        return res

    def _amunet_create_combo_conversion(self, combo_moves, combo_loc):
        self.ensure_one()
        # Operación interna automática: usar sudo para no depender de los
        # permisos del usuario que validó la recepción.
        env = self.env.sudo()
        Move = env['stock.move']
        Lot = env['stock.lot']
        loc_virtual = self._amunet_combo_virtual_location()
        pt = self._amunet_combo_conversion_type()
        wh = self._amunet_combo_warehouse()
        lot_stock = wh.lot_stock_id
        qc_loc = wh.wh_qc_stock_loc_id or lot_stock
        # combo_loc = ENTRADA del almacen (donde aterrizo el combo). De ahi se
        # consume; las hojas salen a Control de calidad (cuarentena).

        # el encabezado debe tener origen != destino (constraint amunet_lot);
        # los movimientos individuales llevan sus ubicaciones reales.
        conv = env['stock.picking'].create({
            'picking_type_id': pt.id,
            'location_id': combo_loc.id,
            'location_dest_id': loc_virtual.id,
            'origin': _('Conversión combo %s') % self.name,
        })

        for cm in combo_moves:
            components = cm.product_id.product_tmpl_id.combo_component_ids
            if not components:
                raise UserError(_(
                    'El combo %s no tiene componentes configurados para '
                    'convertir. Configúralos en la ficha del producto, '
                    'pestaña "Combo de compra".') % cm.product_id.display_name)
            # por cada linea recibida del combo (hereda datos de proveedor)
            for ml in cm.move_line_ids.filtered(lambda l: l.quantity > 0):
                combo_lot = ml.lot_id  # puede NO existir: el combo no lleva lote
                qty = ml.quantity
                # Los datos del proveedor (lote de proveedor + fechas) viven en la
                # LINEA de recepcion (factory_lot_id/manufacturing_date/
                # expiration_date), poblados por amunet_recepcion_materiales exista
                # o no un lote Amunet. El combo NO debe llevar lote Amunet; el lote
                # nace en la hoja individual al convertir.
                factory = ml.factory_lot_id.id if ml.factory_lot_id else False
                fab = ml.manufacturing_date
                exp = ml.expiration_date
                # 1) consumir el combo: ENTRADA -> virtual
                out = Move.create({
                    'product_id': cm.product_id.id,
                    'product_uom_qty': qty, 'product_uom': cm.product_uom.id,
                    'location_id': combo_loc.id,
                    'location_dest_id': loc_virtual.id,
                    'picking_id': conv.id,
                    'description_picking': cm.product_id.display_name,
                })
                out._action_confirm()
                out.move_line_ids.unlink()
                mlvals = {'move_id': out.id, 'product_id': cm.product_id.id,
                          'product_uom_id': cm.product_uom.id,
                          'location_id': combo_loc.id,
                          'location_dest_id': loc_virtual.id, 'quantity': qty}
                if combo_lot:
                    mlvals['lot_id'] = combo_lot.id
                env['stock.move.line'].create(mlvals)
                # 2) producir cada hoja: virtual -> Existencias, lote Amunet
                for comp in components:
                    hoja = comp.product_id
                    hqty = qty * (comp.qty or 1.0)
                    tmpl = hoja.product_tmpl_id
                    lot_name = tmpl.lot_sequence_id.next_by_id() \
                        if tmpl.lot_sequence_id else False
                    # Hoja que requiere QC -> a Control de calidad; el lote nace
                    # 'pending' (Calidad lo libera). Si no requiere -> Existencias.
                    requires_qc = tmpl._amunet_effective_requires_quarantine()
                    dest_loc = qc_loc if requires_qc else lot_stock
                    lot = Lot.create({
                        'product_id': hoja.id,
                        'company_id': self.company_id.id,
                        'name': lot_name or (self.name + '/' + (hoja.default_code or '')),
                        'factory_lot_id': factory,
                        'manufacturing_date': fab,
                        'expiration_date': exp,
                    })
                    inm = Move.create({
                        'product_id': hoja.id, 'product_uom_qty': hqty,
                        'product_uom': hoja.uom_id.id,
                        'location_id': loc_virtual.id,
                        'location_dest_id': dest_loc.id,
                        'picking_id': conv.id,
                        'description_picking': hoja.display_name,
                    })
                    inm._action_confirm()
                    inm.move_line_ids.unlink()
                    env['stock.move.line'].create({
                        'move_id': inm.id, 'product_id': hoja.id,
                        'product_uom_id': hoja.uom_id.id,
                        'location_id': loc_virtual.id,
                        'location_dest_id': dest_loc.id,
                        'quantity': hqty, 'lot_id': lot.id,
                        'factory_lot_id': factory,
                        'manufacturing_date': fab,
                        'expiration_date': exp,
                    })
        conv.action_assign()
        conv.message_post(body=_(
            'Segundo ingreso (conversión de combo) generado desde %s. '
            'Valídalo para que ingresen las hojas individuales con su '
            'lote Amunet.') % self.name)
        self.message_post(body=_(
            'Se generó el 2º ingreso de conversión: %s (combo → hojas).')
            % conv.name)
        return conv
