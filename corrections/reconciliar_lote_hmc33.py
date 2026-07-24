# Reconciliacion del lote HMC33072601 (SPHMC33, Hoja Maestra CA 125, 60 cm).
# El lote ingreso (AMP/IN/00212, 20-jul) ANTES de que el analisis de calidad
# estuviera configurado en Odoo; en la realidad ya fue analizado y liberado fuera
# del sistema. Se reconcilia Odoo con la realidad:
#  1. Traslado interno Control de calidad -> AMP/Existencias.
#  2. Marcar el lote como 'released' (con nota, sin snapshot QC porque no hubo
#     analisis en el sistema).
#  3. Archivar el analisis QC/2026/00021 (estaba en borrador) con nota explicativa.
# Autorizado por Fernando 2026-07-27 (solo HMC33; los demas de esa recepcion siguen
# pendientes de analisis real).
from odoo import fields as _f
from markupsafe import Markup
NOTA = ('Lote ingreso antes de configurar el analisis de calidad en Odoo; '
        'analizado y liberado FUERA del sistema. Reconciliacion manual autorizada '
        'por Fernando 2026-07-27.')

lot = env['stock.lot'].sudo().browse(1941)
assert lot.name == 'HMC33072601', 'lote incorrecto'
qc = env['amunet.quality.check'].sudo().search([('lot_id', '=', lot.id)], limit=1)

# 1) traslado interno Control de calidad (7) -> AMP/Existencias (5)
CC = env['stock.location'].browse(7); EXIST = env['stock.location'].browse(5)
ptype = env['stock.picking.type'].sudo().search([('code', '=', 'internal'), ('warehouse_id.code', '=', 'AMP')], limit=1)
env.cr.execute("SELECT sum(quantity) FROM stock_quant WHERE lot_id=%s AND location_id=%s", (lot.id, CC.id))
qty = env.cr.fetchone()[0] or 0.0
print('En cuarentena:', qty)
if qty > 0:
    pick = env['stock.picking'].sudo().create({
        'picking_type_id': ptype.id, 'location_id': CC.id, 'location_dest_id': EXIST.id,
        'origin': 'Reconciliacion liberacion HMC33072601 (ingreso pre-config analisis)',
        'move_ids': [(0, 0, {'product_id': lot.product_id.id, 'product_uom_qty': qty,
            'product_uom': lot.product_id.uom_id.id, 'location_id': CC.id, 'location_dest_id': EXIST.id})]})
    pick.action_confirm(); pick.action_assign()
    if pick.move_line_ids:
        for ml in pick.move_line_ids:
            ml.lot_id = lot.id; ml.quantity = qty
    else:
        env['stock.move.line'].create({'picking_id': pick.id, 'move_id': pick.move_ids[0].id,
            'product_id': lot.product_id.id, 'product_uom_id': lot.product_id.uom_id.id,
            'location_id': CC.id, 'location_dest_id': EXIST.id, 'lot_id': lot.id, 'quantity': qty})
    pick.with_context(skip_backorder=True).button_validate()
    print('Traslado:', pick.name, pick.state)

# 2) marcar released (manual, documentado)
lot.with_context(skip_lot_release_lock=True).write({
    'amunet_lot_release_state': 'released',
    'amunet_lot_release_notes': NOTA,
    'amunet_lot_released_by_id': env.user.id,
    'amunet_lot_released_date': _f.Datetime.now(),
})
lot.message_post(body=Markup('<b>Lote liberado por reconciliacion manual.</b><br/>' + NOTA))

# 3) archivar la QC borrador con nota
if qc:
    qc.message_post(body=Markup('Analisis archivado sin realizar en el sistema: ' + NOTA))
    qc.active = False
    print('QC archivada:', qc.name)

env.cr.commit()

# verificacion
l2 = env['stock.lot'].sudo().browse(1941)
print('release_state:', l2.amunet_lot_release_state)
env.cr.execute("SELECT sl.complete_name, sq.quantity FROM stock_quant sq JOIN stock_location sl ON sl.id=sq.location_id WHERE sq.lot_id=1941 AND sq.quantity<>0 AND sl.usage='internal'")
print('ubicacion:', env.cr.fetchall())
print('LISTO')
