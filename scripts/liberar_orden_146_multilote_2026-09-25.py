"""Marca la exencion de multi-lote en 0926/01/CRD para desatorar a Almacen.

Mery la autorizo el 25-sep-2026: la orden pide 3,640 viales STBTR02 y ningun
lote alcanza (el mayor tiene 3,535 y esta comprometido con otra orden).
"""
from odoo.exceptions import UserError
mo = env['mrp.production'].search([('name','=','0926/01/CRD')], limit=1)
buf = mo.move_raw_ids.filtered(lambda m: m.product_id.default_code == 'STBTR02')
lotes = buf.move_line_ids.filtered(lambda l: l.lot_id and l.quantity > 0).mapped('lot_id')
print('ANTES: exencion=%s  el candado bloquea?' % mo.amunet_permitir_multi_lote)
try:
    mo.move_raw_ids._amunet_check_single_lot_per_component()
    print('   no bloquea')
except UserError:
    print('   SI bloquea')

mo.write({
    'amunet_permitir_multi_lote': True,
    'amunet_multi_lote_motivo': (
        'La orden pide 3,640 viales STBTR02 y ningun lote alcanza: el mayor '
        '(BTR02082601, 3,535) esta comprometido con otra orden. Se surte con '
        'BTR02092601 (1,999) + BTR02092602 (1,399). Autorizado por Mery.'),
})
mo.message_post(body=(
    'Autorizado el uso de <b>mas de un lote</b> en el componente STBTR02 '
    '(viales de solucion de corrimiento), el 25-sep-2026.<br/><br/>'
    'Motivo: la orden pide <b>3,640 viales</b> y ningun lote alcanza. El mayor '
    '(BTR02082601, 3,535 pz) esta comprometido con otra orden. Se surte con '
    '<b>BTR02092601</b> (1,999) y <b>BTR02092602</b> (1,399).<br/><br/>'
    'Autorizado por Mery. La exencion es solo para esta orden: las demas '
    'siguen con el candado de un lote por componente.'))
env.cr.commit()
print('DESPUES: exencion=%s' % mo.amunet_permitir_multi_lote)
try:
    mo.move_raw_ids._amunet_check_single_lot_per_component()
    print('   el candado YA DEJA PASAR')
except UserError as e:
    print('   *** SIGUE BLOQUEANDO: %s ***' % str(e)[:80])
print('\nlotes autorizados: %s' % ', '.join(lotes.mapped('name')))
print('estado de la orden: %s  (Almacen confirma el surtido y cierra)' % mo.state)
