# Cancela seis liberaciones de Control de calidad que llevaban entre 32 y 167
# dias sin poder validarse. Autorizado por Mery el 28-sep-2026, despues de que
# Karla (Almacen MP) revisara las 12 pendientes una por una.
#
# POR QUE NO SE PUEDEN VALIDAR: las seis piden sacar material de una ubicacion
# donde YA NO ESTA. El material entro y se consumio por otras vias -ajustes de
# inventario, solicitudes de material, ordenes de produccion- y el documento se
# quedo colgado. Validarlas es imposible y dejarlas ahi ensucia la lista de
# pendientes de Almacen, que es donde se busca lo que de verdad falta hacer.
#
# NINGUNA tiene analisis de Calidad ligado (amunet_disposition_qc_id vacio), asi
# que cancelarlas no deja huerfano ningun registro. Tampoco mueven inventario:
# no estan validadas.
#
# El motivo queda escrito en el chatter de cada una: es un registro ISO 13485 y
# tiene que poder explicarse dentro de un ano.
from odoo import fields

CASOS = {
    'AMP/QC/00336': 'Placa de Elisa COPLE01. El material entro y hoy hay 592 pz '
                    'repartidas entre AMP/Existencias y AMPB/Existencias; se ha '
                    'venido consumiendo por solicitudes de material, la ultima el '
                    '23-sep-2026. En AMP/Entrada no queda nada que liberar.',
    'AMP/QC/00358': 'Caja Caple HEMOGLINET MICAJ19, 2,350 pz. El material ya se '
                    'consumio en tres ordenes de fabricacion: 0626/01/HBC (100 pz), '
                    '0826/01/HBC (1,326 pz) y 0726/01/HBC (634 pz). Quedan 70 pz en '
                    'AMP/Existencias. Confirmado por Karla el 28-sep-2026.',
    'AMP/QC/00368': 'Cofias y guantes (COGEC01, COGME01, COCOF01). Salieron por '
                    'solicitudes de material, la ultima el 28-sep-2026. En '
                    'AMP/Entrada no queda existencia.',
    'AMP/QC/00388': 'Combo antidoping sangre D000-4055, 30 pz. Sale de la ubicacion '
                    'virtual "Conversion de combos", donde no hay existencia. '
                    'Relacionada con CONV/00005.',
    'AMP/QC/00390': 'Combo mosquito I163-4045, 30 pz. Sin existencia en AMP/Entrada. '
                    'Viene de la recepcion AMP/IN/00296.',
    'AMP/QC/00400': 'Combo antidoping sangre D000-4055. Pide 8,970 pz cuando en el '
                    'origen hay 30, y va al reves que todas las demas '
                    '(Control de calidad -> AMP/Entrada). La cantidad corresponde a '
                    'una compra completa (P00213), no a un muestreo: el documento '
                    'nacio mal. Se cancela; si hace falta liberar ese material se '
                    'genera uno nuevo con la cantidad correcta.',
}

P = env['stock.picking'].sudo()
print('%-14s %-10s %s' % ('DOCUMENTO', 'ANTES', 'RESULTADO'))
for nombre, motivo in CASOS.items():
    p = P.search([('name', '=', nombre)], limit=1)
    if not p:
        print('%-14s %-10s NO EXISTE' % (nombre, '-')); continue
    if p.state in ('done', 'cancel'):
        print('%-14s %-10s ya estaba, no se toca' % (nombre, p.state)); continue
    # Guardas: no cancelar nada que tenga analisis ligado ni material disponible.
    qc = getattr(p, 'amunet_disposition_qc_id', False)
    assert not qc, '%s tiene ligado el analisis %s: revisar a mano' % (nombre, qc.name if qc else '')
    for m in p.move_ids:
        hay = sum(env['stock.quant'].sudo().search([
            ('product_id', '=', m.product_id.id),
            ('location_id', 'child_of', m.location_id.id)]).mapped('quantity'))
        assert hay < m.product_uom_qty, (
            '%s: %s SI tiene material suficiente (%s de %s). No es un fantasma, '
            'se valida en vez de cancelarse.' % (nombre, m.product_id.default_code,
                                                 hay, m.product_uom_qty))
    antes = p.state
    p.message_post(body=(
        'Documento <b>cancelado</b> por Desarrollo, autorizado por Mery.<br/><br/>'
        '<b>Motivo:</b> lleva %(dias)s dias sin poder validarse porque el material '
        'ya no esta en la ubicacion de origen.<br/><br/>%(detalle)s<br/><br/>'
        'No mueve inventario -no estaba validado- y no tiene analisis de Calidad '
        'ligado, asi que no deja ningun registro huerfano. Revisado por Karla '
        '(Almacen MP) el 28-sep-2026.'
    ) % {'dias': (fields.Datetime.now() - p.create_date).days, 'detalle': motivo})
    p.action_cancel()
    p.invalidate_recordset()
    print('%-14s %-10s -> %s' % (nombre, antes, p.state))

env.cr.commit()
print()
print('=== liberaciones que quedan pendientes ===')
for p in P.search([('name', 'like', 'AMP/QC/'), ('state', 'not in', ('done', 'cancel'))], order='name'):
    print('  %-14s %-10s %s' % (p.name, p.state,
          ', '.join(p.move_ids.mapped('product_id.default_code'))[:40]))
