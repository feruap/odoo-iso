"""Configura el prefijo de lote de los productos que no lo tienen.

Autorizado por Mery el 28-sep-2026.

EL PROBLEMA: 39 productos que llevan lote y se reciben o se fabrican comparten la
secuencia GENERICA de Odoo ("Serial Numbers", id 15, sin prefijo) en vez de tener
la suya. Cuando Almacen los recibe, el lote sale como "0000001" en lugar de su
prefijo. Es lo que paso con MPAGE04 en AMP/IN/00478, y de ahi vienen los 117 lotes
"0000001" que hay hoy en el catalogo.

Entre los 39 hay NUEVE de las soluciones que el area va a probar (SPACL01,
SPCDS01, SPSAC02, SPSCS01, SPSHS03, SPSPA04, SPSPA05, SPSPV01 y STDES01): si se
fabrican asi, cada lote nace con un consecutivo tonto y luego hay que renombrarlo
a mano, con analisis encima. Por eso se arregla ANTES de la prueba.

COMO: se escribe `amunet_lot_prefix` en el producto y el propio modulo crea la
secuencia con su patron (PREFIJO + mes + anio, padding 2) y la liga al producto.
No se toca la secuencia 15: la comparten 354 productos.

EL PREFIJO sale de la normativa de codificacion: la clave sin las dos primeras
letras de clasificacion. SPALMA14 -> ALMA14, MPREC98 -> REC98, COAGI01 -> AGI01.

QUEDAN FUERA a proposito los productos cuya clave NO sigue la normativa Amunet
(codigos de proveedor como BECPSAS103 o GRCTPS206): ahi el prefijo no se puede
deducir y lo tiene que asignar Documentacion. Se listan al final.

Idempotente: solo toca los que no tienen prefijo.
"""

PT = env['product.template'].sudo()
CLASIFICACIONES = ('MP', 'MI', 'SP', 'ST', 'PT', 'CO', 'EQ', 'DM', 'DL', 'DR')

candidatos = PT.search([('tracking', 'in', ('lot', 'serial'))])
sin_prefijo = candidatos.filtered(
    lambda t: not (t.lot_sequence_id and (t.lot_sequence_id.prefix or '').strip()))
# Los productos terminados llevan el lote que les pone su orden de fabricacion,
# con su propio numerador; no dependen de esta secuencia.
sin_prefijo = sin_prefijo.filtered(
    lambda t: not (t.categ_id.complete_name or '').startswith('Producto terminado'))
print('productos que llevan lote, se reciben o fabrican, y no tienen prefijo: %s'
      % len(sin_prefijo))

hechos, fuera, colisiones = [], [], []
for t in sin_prefijo.sorted(lambda x: x.default_code or ''):
    clave = (t.default_code or '').strip()
    # Fuera: sin clave, clave que no sigue la normativa, o clave con punto. Las
    # claves con punto son variantes por unidad (MPABI01.ml, MPATR01.ml) y darian
    # un prefijo de lote con punto -- "ABI01.ml092601" --, que no es aceptable en
    # una etiqueta. Esas necesitan que Documentacion diga su prefijo.
    if (len(clave) < 5 or clave[:2] not in CLASIFICACIONES
            or not clave[2:].strip() or '.' in clave):
        fuera.append((clave or '(sin clave)', t.name))
        continue
    prefijo = clave[2:]
    # La colision se busca en las SECUENCIAS: amunet_lot_prefix es un campo
    # calculado con inverse y no se puede buscar (no esta almacenado).
    patron = '%s%%(month)s%%(y)s' % prefijo
    otra_seq = env['ir.sequence'].sudo().search(
        [('prefix', '=', patron)], limit=1)
    if otra_seq:
        duenos = PT.search([('lot_sequence_id', '=', otra_seq.id), ('id', '!=', t.id)])
        if duenos:
            colisiones.append((clave, prefijo, ', '.join(duenos.mapped('default_code')[:3])))
    t.write({'amunet_lot_prefix': prefijo})
    seq = t.lot_sequence_id
    hechos.append((clave, prefijo, seq.prefix if seq else '?', seq.id if seq else 0))

print('\n=== CONFIGURADOS (%s) ===' % len(hechos))
for clave, prefijo, patron, sid in hechos:
    print('   %-12s -> %-9s secuencia %-6s %s' % (clave, prefijo, sid, patron))

if colisiones:
    print('\n=== OJO: prefijo que ya usa otro producto (%s) ===' % len(colisiones))
    print('   (no estorba: el nombre de lote es unico POR PRODUCTO, pero conviene revisarlo)')
    for clave, prefijo, otro in colisiones:
        print('   %-12s prefijo %-9s ya lo usa %s' % (clave, prefijo, otro))

if fuera:
    print('\n=== FUERA: su clave no sigue la normativa, el prefijo lo asigna Documentacion (%s) ===' % len(fuera))
    for clave, nombre in fuera:
        print('   %-12s %s' % (clave, (nombre or '')[:52]))

print('\n=== comprobacion: cuantos quedan sin prefijo ===')
faltan = PT.search([('tracking', 'in', ('lot', 'serial'))]).filtered(
    lambda t: not (t.lot_sequence_id and (t.lot_sequence_id.prefix or '').strip())
    and not (t.categ_id.complete_name or '').startswith('Producto terminado'))
print('   %s (deberian ser los %s de la lista de arriba)' % (len(faltan), len(fuera)))
env.cr.commit()
