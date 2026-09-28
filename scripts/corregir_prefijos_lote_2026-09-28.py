# Corrige el prefijo de lote de 19 productos cuyo prefijo no cuadra con la
# convencion: el prefijo es la CLAVE SIN LAS DOS PRIMERAS LETRAS de
# clasificacion (MPCAR24 -> CAR24, SPHMC85 -> HMC85). Autorizado por Mery el
# 28-sep-2026, a raiz de que los lotes nuevos de STCPL04 salieran como
# PL04092601 en vez de CPL04092601.
#
# DOS FAMILIAS, DOS ERRORES DISTINTOS:
#
# 1. STCPL01..STCPL16 (controles positivos): se quitaron TRES letras en vez de
#    dos, y quedo PL## donde va CPL##. Los lotes de junio a agosto si nacieron
#    bien (CPL04062601, CPL04082601...), asi que la configuracion se rompio
#    entre agosto y septiembre.
#
# 2. SPALMA11, 12 y 13 (almohadillas): el prefijo esta CORRIDO UN NUMERO.
#    SPALMA12 usa ALMA11, que es el prefijo de SPALMA11. Dos productos podrian
#    generar lotes con el mismo prefijo, y los lotes ya creados dicen pertenecer
#    al producto de al lado. Esto no es cosmetico: es identificacion equivocada
#    de material.
#
# NO se toca LEN01 (Lengueta): su clave no sigue el patron de dos letras de
# clasificacion, asi que la regla no le aplica y su prefijo esta bien.
#
# COMO: se reescribe la secuencia YA LIGADA al producto, en vez de escribir
# amunet_lot_prefix. El inverse de ese campo busca la secuencia por un codigo
# que incluye el prefijo; al cambiarlo no la encuentra, CREA una nueva y deja
# la vieja huerfana. Reescribirla en su lugar conserva el vinculo y no duplica.
#
# El contador no importa: _amunet_next_lot_names calcula el numero a partir del
# maximo lote existente del periodo, no del contador de la secuencia.
CLAVES = ['STCPL%02d' % i for i in range(1, 17)] + ['SPALMA11', 'SPALMA12', 'SPALMA13']

T = env['product.template'].sudo()
print('%-10s %-10s %-10s %s' % ('CLAVE', 'ANTES', 'AHORA', 'SECUENCIA'))
tocados = 0
for cod in CLAVES:
    t = T.search([('default_code', '=', cod)], limit=1)
    if not t:
        print('%-10s %-10s %-10s no existe' % (cod, '-', '-')); continue
    esperado = cod[2:]
    antes = (t.amunet_lot_prefix or '').strip()
    if antes == esperado:
        print('%-10s %-10s %-10s ya estaba bien' % (cod, antes, esperado)); continue
    seq = t.lot_sequence_id
    assert seq, '%s no tiene secuencia ligada: revisar a mano' % cod
    seq.sudo().write({
        'prefix': '%s%%(month)s%%(y)s' % esperado,
        'code': 'amunet.lot.%s.%s' % (esperado, t.id),
        'name': 'Lote %s - %s' % (esperado, t.name),
    })
    t.invalidate_recordset()
    print('%-10s %-10s %-10s %s' % (cod, antes, t.amunet_lot_prefix or '?', seq.prefix))
    tocados += 1

env.cr.commit()
print()
print('corregidos: %s de %s' % (tocados, len(CLAVES)))
print()
print('=== comprobacion: como se llamaria el proximo lote de cada uno ===')
for cod in ('STCPL04', 'STCPL14', 'SPALMA11', 'SPALMA12', 'SPALMA13'):
    t = T.search([('default_code', '=', cod)], limit=1)
    pv = t.product_variant_ids[:1]
    try:
        print('  %-10s -> %s' % (cod, pv._amunet_next_lot_names(1)[0]))
    except Exception as e:
        print('  %-10s -> no se pudo calcular: %s' % (cod, str(e)[:60]))
