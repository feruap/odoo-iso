# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class ProductionPlanShortage(models.Model):
    _inherit = 'amunet.production.plan.shortage'

    # Marca de trazabilidad: la OC generada para este faltante (evita duplicar
    # la requisicion si el boton se corre dos veces).
    purchase_order_id = fields.Many2one(
        'purchase.order', string='Orden de compra generada',
        readonly=True, copy=False, index=True)


class ProductionPlan(models.Model):
    _inherit = 'amunet.production.plan'

    def action_create_purchase_requisition(self):
        """Crea ordenes de compra en BORRADOR desde los faltantes del plan,
        agrupadas por proveedor. Reglas:
          - Solo los faltantes que tienen proveedor (seller_id) van a compra.
          - Los que NO tienen proveedor (se fabrican, ej. hojas maestras) se
            reportan aparte y NO se compran.
          - Las OC se crean SIN PRECIO (restriccion de precios: solo Fernando
            los ve/pone). Compras/Fernando fija precio y confirma.
        """
        self.ensure_one()
        self.invalidate_recordset(['shortage_ids'])
        pendientes = self.shortage_ids.filtered(
            lambda s: s.qty_missing > 0 and not s.purchase_order_id)
        if not pendientes:
            raise UserError(_(
                'No hay faltantes pendientes de requisicion en este plan.'))

        # El "proveedor" auto = la propia compania (Amunet) NO cuenta: esos
        # materiales se FABRICAN en casa (hojas maestras, soluciones), no se
        # compran. Se tratan igual que los sin proveedor.
        self_partner = self.company_id.partner_id
        con_prov = pendientes.filtered(
            lambda s: s.seller_id and s.seller_id != self_partner)
        sin_prov = pendientes - con_prov
        if not con_prov:
            raise UserError(_(
                'Ninguno de los faltantes pendientes tiene proveedor externo. '
                'Los que se fabrican (hojas maestras, etc.) necesitan orden de '
                'fabricacion, no compra.'))

        Purchase = self.env['purchase.order']
        POL = self.env['purchase.order.line']
        Shortage = self.env['amunet.production.plan.shortage']
        created = Purchase.browse()

        por_prov = {}
        for s in con_prov:
            por_prov.setdefault(s.seller_id.id, Shortage)
            por_prov[s.seller_id.id] |= s

        for seller_id, items in por_prov.items():
            po = Purchase.create({
                'partner_id': seller_id,
                'origin': self.name,
                'company_id': self.company_id.id,
            })
            for s in items:
                prod = s.product_id
                POL.create({
                    'order_id': po.id,
                    'product_id': prod.id,
                    'name': prod.display_name,
                    'product_qty': s.qty_missing,
                    'product_uom_id': prod.uom_id.id,
                    'price_unit': 0.0,  # sin precio: restriccion de compras
                    'date_planned': fields.Datetime.now(),
                })
                s.purchase_order_id = po.id
            created |= po

        msg = _('Se crearon %s ordenes de compra en borrador (sin precio), '
                'agrupadas por proveedor.') % len(created)
        if sin_prov:
            det = ', '.join(
                '%s (%s)' % (s.product_id.default_code or s.product_id.display_name,
                             int(s.qty_missing)) for s in sin_prov[:30])
            msg += _('\n\nNO incluidos en compra (sin proveedor: se fabrican o '
                     'falta asignarles proveedor): %s') % det
        self.message_post(body=msg)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Ordenes de compra generadas'),
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', created.ids)],
        }
