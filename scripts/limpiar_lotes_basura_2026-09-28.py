"""Borra los lotes con nombre de consecutivo tonto que no tienen NADA colgando.

Autorizado por Mery el 28-sep-2026.

DE DONDE SALEN: cuando un producto que lleva lote no tiene su prefijo configurado,
Odoo usa la secuencia generica y el lote nace como "0000001". Hay 117 asi. La causa
ya se cerro el mismo dia (se configuro el prefijo de 29 productos), asi que no se
van a generar mas.

DE LOS 117, SOLO SE BORRAN LOS QUE NO TIENEN NADA:

    21 sin movimientos, sin existencia y sin analisis  ->  se borran
    96 CON MOVIMIENTOS VALIDADOS                       ->  NO se tocan

Los 96 tienen movimientos en estado 'done' ligados a recepciones reales
(AMP/IN/00340, AMP/IN/00296, CONV/00007...). Ese material entro al almacen con ese
lote: borrarlo romperia la trazabilidad de recepciones ya validadas, que es
requisito ISO 13485. Tampoco se pueden archivar -- stock.lot no tiene campo active
en Odoo 19 --, asi que se quedan como testimonio de lo que paso.

Renombrarlos tampoco procede: cambiaria la identidad de lotes con movimientos
validados, que es justo lo que el sistema impide para lotes liberados.

Ninguno de los 117 tiene existencia, asi que no hay material perdido en ellos.

Idempotente.
"""
import re

Lot = env['stock.lot'].sudo()
MoveLine = env['stock.move.line'].sudo()
Quant = env['stock.quant'].sudo()
Check = env['amunet.quality.check'].sudo()

basura = Lot.search([]).filtered(
    lambda l: re.fullmatch(r'0+\d*', (l.name or '').strip()))
print('lotes con nombre de consecutivo tonto: %s' % len(basura))

borrados, retenidos = [], []
for l in basura:
    mov = MoveLine.search_count([('lot_id', '=', l.id)])
    qc = Check.with_context(active_test=False).search_count([('lot_id', '=', l.id)])
    stock = sum(Quant.search([('lot_id', '=', l.id)]).mapped('quantity'))
    motivo = []
    if abs(stock) > 0.0001:
        motivo.append('existencia %g' % stock)
    if qc:
        motivo.append('%s analisis' % qc)
    if mov:
        motivo.append('%s movimiento(s) validado(s)' % mov)
    if motivo:
        retenidos.append((l.product_id.default_code or '?', l.name, '; '.join(motivo)))
        continue
    datos = (l.product_id.default_code or '?', l.name)
    try:
        l.unlink()
        borrados.append(datos)
    except Exception as e:
        retenidos.append((datos[0], datos[1], 'no se pudo borrar: %s' % str(e)[:70]))

print('\n=== BORRADOS (%s) ===' % len(borrados))
for c, n in sorted(borrados):
    print('   %-20s %s' % (c, n))

print('\n=== NO SE TOCAN (%s) — su historial se conserva ===' % len(retenidos))
from collections import Counter
razones = Counter(r.split(';')[0].split(' ')[1] if 'movimiento' in r else r.split(';')[0]
                  for _, _, r in retenidos)
for r, n in razones.most_common():
    print('   %s lote(s): %s' % (n, r))
print('   productos distintos afectados: %s' % len(set(c for c, _, _ in retenidos)))

env.cr.commit()
print('\nquedan %s lotes con nombre de consecutivo tonto (los que tienen historial)'
      % len(Lot.search([]).filtered(lambda l: re.fullmatch(r'0+\d*', (l.name or '').strip()))))
