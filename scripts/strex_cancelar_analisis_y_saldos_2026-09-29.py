"""Cierra el caso STREX: archiva los dos analisis y corrige sus saldos.

Pedido por Diana el 29-sep-2026 a las 18:41, autorizado por Mery. Cierra un caso
abierto desde el 24-sep.

LO QUE DIJO CALIDAD: los dos lotes se crearon por un error de clasificacion. El
material recibido en AMP/IN/00168 correspondia a la clave SPHMC87, no a STREX, y el
ajuste del 30 de julio que lo saco de cuarentena formo parte de esa correccion. No
existe material fisico que respaldar.

    QC/2026/00346   id 674   STREX01   lote REX01062605
    QC/2026/00348   id 675   STREX02   lote REX02062603

SE ARCHIVAN, NO SE "CANCELAN": amunet.quality.check no tiene estado 'cancel' -- sus
estados son draft, in_progress, pending, awaiting_reception y done. Archivar
(active=False) es el equivalente en este modelo y es como se ha hecho antes; el
registro se conserva para el expediente y deja de aparecer en las vistas.

LOS SALDOS: cada lote tiene -1 en AMP/Existencias y +1 en Control de calidad. Son las
dos mitades del MISMO movimiento fantasma: la muestra que el analisis mando a
cuarentena desde existencias, donde no habia material. Diana pidio corregir el
negativo; se corrigen LAS DOS, porque dejar el +1 en cuarentena sin analisis que lo
justifique seria dejar material que no existe esperando una liberacion que nunca va a
llegar. El neto del lote no cambia: era cero y sigue en cero.

Idempotente.
"""
from markupsafe import Markup

Check = env['amunet.quality.check'].sudo()
Quant = env['stock.quant'].sudo()

NOTA = ('Análisis cancelado: lote creado por error de clasificación. El material '
        'recibido en AMP/IN/00168 correspondía a la clave SPHMC87, no a STREX. El '
        'ajuste del 30 de julio que lo sacó de cuarentena formó parte de esa '
        'corrección. No existe material físico que respaldar. Saldo negativo en '
        'inventario pendiente de corrección por almacén.')
RAZON = ('Cancelacion pedida por Calidad (Diana) el 29-sep-2026 y autorizada por Mery: '
         'lote creado por error de clasificacion, sin material fisico que respaldar.')

print('-- 1. los dos analisis --')
for cid, folio in ((674, 'QC/2026/00346'), (675, 'QC/2026/00348')):
    qc = Check.with_context(active_test=False).browse(cid)
    if not qc.exists():
        print('   [ojo] no existe el analisis %s' % cid); continue
    if qc.name != folio:
        # el id se confirmo en produccion; si en otra base apunta a otro folio, no se toca
        print('   [ALTO] el id %s es %s, no %s -- no se toca' % (cid, qc.name, folio)); continue
    if not qc.active:
        print('   [ya] %s ya esta archivado' % qc.name); continue
    print('   %s  %s  lote %s  estado %s' % (
        qc.name, qc.product_id.default_code, qc.lot_id.name or '-', qc.state))
    qc.message_post(body=Markup('%s<br/><br/><i>Nota textual de Calidad (Diana), '
                                '29-sep-2026.</i>') % NOTA)
    qc.write({'active': False, 'change_reason': RAZON})
    print('   [ok] %s archivado' % qc.name)

print('\n-- 2. los saldos fantasma --')
for clave, nombre_lote in (('STREX01', 'REX01062605'), ('STREX02', 'REX02062603')):
    prod = env['product.product'].sudo().search([('default_code', '=', clave)], limit=1)
    lote = env['stock.lot'].sudo().search(
        [('name', '=', nombre_lote), ('product_id', '=', prod.id)], limit=1)
    if not prod or not lote:
        print('   [ojo] falta %s o su lote %s' % (clave, nombre_lote)); continue
    quants = Quant.search([('product_id', '=', prod.id), ('lot_id', '=', lote.id),
                           ('location_id.usage', '=', 'internal')]).filtered(
        lambda q: abs(q.quantity) > 0.0001)
    if not quants:
        print('   [ya] %s lote %s ya esta en cero en todas las ubicaciones' % (
            clave, nombre_lote)); continue
    for q in quants:
        antes = q.quantity
        q.with_context(inventory_mode=True).write({'inventory_quantity': 0.0})
        q.with_context(inventory_mode=True).action_apply_inventory()
        print('   [ok] %s lote %s: %g -> 0 en %s' % (
            clave, nombre_lote, antes, q.location_id.complete_name))
    lote.message_post(body=Markup(
        'Saldos puestos en cero el 29-sep-2026, autorizado por Mery a peticion de '
        'Calidad.<br/><br/>Este lote se creo por un <b>error de clasificacion</b>: el '
        'material recibido en AMP/IN/00168 era de la clave SPHMC87, no de STREX. Su '
        'analisis (%s) quedo archivado el mismo dia.<br/><br/>Tenia <b>-1 en '
        'existencias y +1 en Control de calidad</b>: las dos mitades del mismo '
        'movimiento fantasma -- la muestra que el analisis mando a cuarentena desde '
        'existencias, donde no habia material. No existe material fisico que '
        'respaldar, asi que las dos quedan en cero.'
    ) % ('QC/2026/00346' if clave == 'STREX01' else 'QC/2026/00348'))

print('\n=== como queda ===')
for cid in (674, 675):
    qc = Check.with_context(active_test=False).browse(cid)
    if qc.exists():
        print('   %s  activo=%s  estado=%s' % (qc.name, qc.active, qc.state))
for clave in ('STREX01', 'STREX02'):
    prod = env['product.product'].sudo().search([('default_code', '=', clave)], limit=1)
    neg = Quant.search([('product_id', '=', prod.id),
                        ('location_id.usage', '=', 'internal')]).filtered(
        lambda q: q.quantity < 0)
    tot = sum(Quant.search([('product_id', '=', prod.id),
                            ('location_id.usage', '=', 'internal')]).mapped('quantity'))
    print('   %-8s existencia interna total %g   lotes en negativo: %s' % (
        clave, tot, neg.mapped('lot_id.name') or 'ninguno'))
env.cr.commit()
