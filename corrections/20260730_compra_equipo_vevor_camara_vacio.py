# -*- coding: utf-8 -*-
# Compra de prueba/real del equipo de uso interno VEVOR (camara de vacio 2 gal)
# para ejercitar el flujo de Solicitudes de ingreso de equipo. Precio 0 por la
# restriccion de precios de compras (Fernando captura el costo real si aplica).
from odoo import fields

Prod = env['product.product'].search([('default_code', '=', 'EQUIPO-USO-INTERNO')], limit=1)

partner = env['res.partner'].search([('name', 'ilike', 'vevor')], limit=1)
if not partner:
    partner = env['res.partner'].create({
        'name': 'VEVOR Mexico',
        'company_type': 'company',
        'supplier_rank': 1,
    })
    print("Proveedor creado:", partner.name, partner.id)
else:
    print("Proveedor existente:", partner.name, partner.id)

amp_in_type = env['stock.picking.type'].browse(1)

po = env['purchase.order'].create({
    'partner_id': partner.id,
    'picking_type_id': amp_in_type.id,
    'order_line': [(0, 0, {
        'product_id': Prod.id,
        'name': 'VEVOR Camara de vacio de 2 galones - camara de desgasificacion '
                'al vacio acrilica multiusos (desgasificacion de resina/silicon/'
                'yeso y extraccion al vacio)',
        'product_qty': 1.0,
        'product_uom_id': Prod.uom_id.id,
        'price_unit': 0.0,
        'date_planned': fields.Datetime.now(),
    })],
})
po.button_confirm()

pick = po.picking_ids[:1]
print("PO:", po.name, "| estado:", po.state)
print("Recepcion:", pick.name, "| estado:", pick.state, "| destino:",
      pick.location_dest_id.complete_name, "| producto:", pick.move_ids.product_id.default_code)
env.cr.commit()
