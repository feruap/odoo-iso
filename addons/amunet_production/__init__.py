# -*- coding: utf-8 -*-
from . import models
from . import wizard


def post_init_entrada_interna(env):
    """Cuelga 'Entrada Interna' de AMP y apunta el tipo de operacion.

    El XML no puede referenciar la ubicacion vista del almacen: no tiene
    XMLID en esta base. Se ajusta aqui, donde si se puede preguntar por el
    almacen. Mery, 21-sep-2026.
    """
    almacen = env['stock.warehouse'].search([('code', '=', 'AMP')], limit=1)
    if not almacen:
        return
    loc = env.ref('amunet_production.stock_location_amp_entrada_interna',
                  raise_if_not_found=False)
    if loc and loc.location_id != almacen.view_location_id:
        loc.sudo().write({'location_id': almacen.view_location_id.id})
    tipo = env.ref('amunet_production.picking_type_ingreso_produccion',
                   raise_if_not_found=False)
    if tipo and loc:
        tipo.sudo().write({
            'default_location_src_id': loc.id,
            'default_location_dest_id': almacen.lot_stock_id.id,
            'warehouse_id': almacen.id,
        })
