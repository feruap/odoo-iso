# -*- coding: utf-8 -*-
"""Lotes que nunca tuvieron material: los que gastan consecutivo sin servir de nada.

EL PROBLEMA, visto el 01-oct-2026. La recepcion AMP/IN/00489 puso a las aguas el
consecutivo 02 cuando era el primer lote del mes. El 01 lo habia gastado AMP/IN/00485,
una recepcion de la MISMA solicitud que luego se cancelo: al cancelarla, los lotes que
habia creado se quedaron en la base, vacios, con el numero ya consumido.

Hay 151 lotes asi en produccion. Cada uno deja un hueco en la numeracion que despues
nadie sabe explicar: se busca el lote 01 de un producto, no existe en ningun almacen, y
el material esta en el 02.

QUE CUENTA COMO HUERFANO, y es deliberadamente estricto: un lote que NO tiene
  - ni un solo movimiento de inventario (stock.move.line),
  - ni existencia (stock.quant),
  - ni ninguna referencia desde ningun otro modelo del sistema.

Esa tercera condicion es la importante y se comprueba a lo bruto: se recorren TODOS los
campos many2one que apuntan a stock.lot en todo el sistema -- analisis de calidad,
solicitudes, ordenes de fabricacion, lo que sea, incluido lo que se agregue manana- y se
descarta cualquier lote que aparezca en alguno. Asi el script no depende de que yo me
haya acordado de todos los lugares donde un lote puede estar nombrado.

Un lote que cumple las tres cosas nunca tuvo material fisico: no hay nada que trazar, y
borrarlo no borra historia porque no hay historia.

ANTIGUEDAD MINIMA (dias): un lote creado hoy puede ser de una recepcion en curso que
todavia no asigna sus lineas. Por eso solo se consideran los que llevan DIAS sin que
nadie los use.

DRY_RUN=True por defecto: la primera corrida solo ENSENA lo que haria. Para borrar de
verdad hay que cambiarlo a False a mano, y eso lo decide una persona.
"""

DRY_RUN = True      # en True no borra nada: solo lista
DIAS_MINIMOS = 7    # un lote mas nuevo puede ser de una recepcion en curso

from datetime import datetime, timedelta

corte = datetime.now() - timedelta(days=DIAS_MINIMOS)
Lot = env['stock.lot']

# --- 1) los que no tienen movimiento ni existencia ---
todos = Lot.search([('create_date', '<', corte.strftime('%Y-%m-%d %H:%M:%S'))])
print('lotes con mas de %s dias: %s' % (DIAS_MINIMOS, len(todos)))

con_movs = set(env['stock.move.line'].search([('lot_id', 'in', todos.ids)]).mapped('lot_id').ids)
con_stock = set(env['stock.quant'].search([('lot_id', 'in', todos.ids)]).mapped('lot_id').ids)
candidatos = todos.filtered(lambda l: l.id not in con_movs and l.id not in con_stock)
print('  sin movimientos ni existencia: %s' % len(candidatos))

# --- 2) referencias desde CUALQUIER otro modelo ---
# Se recorren todos los many2one que apuntan a stock.lot. Asi no depende de que yo
# recuerde donde mas puede estar nombrado un lote.
referencias = {}
campos = env['ir.model.fields'].search([
    ('relation', '=', 'stock.lot'), ('ttype', '=', 'many2one'), ('store', '=', True)])
print('\ncampos en el sistema que apuntan a un lote: %s' % len(campos))
for f in campos:
    modelo = f.model
    if modelo in ('stock.move.line', 'stock.quant'):
        continue
    if modelo not in env:
        continue
    try:
        usados = env[modelo].sudo().with_context(active_test=False).search(
            [(f.name, 'in', candidatos.ids)])
    except Exception as e:
        print('   [!] %s.%s no se pudo consultar (%s): se EXCLUYEN todos por precaucion'
              % (modelo, f.name, str(e)[:40]))
        candidatos = Lot.browse()
        break
    if usados:
        ids = set(usados.mapped(f.name).ids)
        for i in ids:
            referencias.setdefault(i, []).append('%s.%s' % (modelo, f.name))
        print('   %-46s %s lote(s) referenciado(s)' % ('%s.%s' % (modelo, f.name), len(ids)))

sin_referencia = candidatos.filtered(lambda l: l.id not in referencias)
atados = candidatos.filtered(lambda l: l.id in referencias)

# LOS EQUIPOS SE SEPARAN, y esto lo enseno la primera simulacion: entre los
# candidatos salieron EQREF01 a EQREF09, EQBSD01, EQINC01, EQMIC01, EQTER01 y otros.
# No son lotes de material: son los numeros de SERIE con que se identifica un equipo
# fisico. Un equipo puede estar dado de alta, calibrado y en uso sin tener un solo
# movimiento de inventario, porque nunca se "mueve" entre almacenes.
#
# De hecho la comprobacion de referencias cazo uno atado a amunet.equipment.serial, lo
# que confirma que los equipos cuelgan de aqui. Borrar la serie de un equipo le quita
# su identificador, y eso en un equipo calibrado es un problema de Cofepris.
#
# Asi que los equipos NO se borran: se listan aparte y los decide una persona.
def es_equipo(lote):
    categoria = (lote.product_id.categ_id.complete_name or '').lower()
    clave = lote.product_id.default_code or ''
    return clave.startswith('EQ') or 'equipo' in categoria

equipos = sin_referencia.filtered(es_equipo)
limpios = sin_referencia - equipos

print('\n=== RESULTADO ===')
print('  candidatos                  : %s' % len(candidatos))
print('  atados a algun modelo       : %s  (NO se tocan)' % len(atados))
print('  series de EQUIPO            : %s  (NO se tocan: son el identificador del equipo)' % len(equipos))
print('  lotes de material huerfanos : %s' % len(limpios))

if atados:
    print('\n  los atados, por si interesa:')
    for l in atados[:10]:
        print('     %-16s %s' % (l.name, ', '.join(referencias[l.id])))

if equipos:
    print('\n  series de equipo que se dejan quietas:')
    for l in equipos.sorted(lambda x: x.product_id.default_code or ''):
        print('     %-10s serie %-16s (creada %s)' % (
            l.product_id.default_code, l.name, str(l.create_date)[:10]))

if limpios:
    print('\n  huerfanos por producto (los 20 primeros productos):')
    por_prod = {}
    for l in limpios:
        por_prod.setdefault(l.product_id.default_code or '?', []).append(l.name)
    for clave in sorted(por_prod)[:20]:
        nombres = sorted(por_prod[clave])
        print('     %-10s %2s lote(s): %s' % (clave, len(nombres), ', '.join(nombres[:5])
                                              + (' ...' if len(nombres) > 5 else '')))
    print('     ... %s productos en total' % len(por_prod))

if DRY_RUN:
    print('\nSIMULACION: no se borro nada. Para borrar, poner DRY_RUN = False.')
else:
    borrados, fallidos = 0, []
    for l in limpios:
        nombre = l.name
        try:
            l.unlink()
            borrados += 1
        except Exception as e:
            fallidos.append((nombre, str(e)[:60]))
    env.cr.commit()
    print('\nBORRADOS: %s' % borrados)
    if fallidos:
        print('NO se pudieron borrar %s (los protege alguna restriccion de la base):' % len(fallidos))
        for nombre, err in fallidos[:10]:
            print('   %-16s %s' % (nombre, err))
    print('quedan sin movimiento ni existencia: %s' % env['stock.lot'].search_count(
        [('id', 'in', limpios.ids)]))
