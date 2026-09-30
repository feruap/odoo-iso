"""Renglones que el analista ve repetidos: se apaga el sobrante y se distinguen los volumenes.

Autorizado por Mery el 30-sep-2026, a partir de un barrido propio -no lo reporto Calidad-.

EL PROBLEMA: 16 bloques de control tienen el MISMO renglon dos veces, y uno siete veces.
El analista abre el analisis, ve "Deformidad o deterioro" dos renglones seguidos y no sabe
cual esta contestando. Es el mismo defecto que Calidad nos reporto en septiembre con
MAVI-16, donde dos renglones distintos mostraban el mismo texto.

SON DOS COSAS DISTINTAS, y se tratan distinto:

1. DUPLICADOS DE VERDAD (13 renglones en 10 productos). El mismo renglon configurado dos
   veces, y una de las dos copias esta mal:
       - criterio VACIO, o
       - criterio igual al nombre del renglon ("Deformidad o deterioro." no es un
         criterio, es el nombre con un punto), o
       - identica a la otra.
   Se DESACTIVA la mala y se conserva la que tiene criterio real. No se borra: borrar un
   renglon del catalogo rompe el historico de cualquier analisis que lo haya usado.

2. SIETE MEDICIONES CON EL MISMO NOMBRE (STCNL01, STCON01, SPCNL04). Aqui NO hay
   duplicados: son siete volumenes DISTINTOS que se llaman todos "Variacion de volumen":
       1000 ul | 2.5 ml | 100-200 ul +-20 | 2 ml +-0.5 | 650 uL +-10 | 500 ul | (uno vacio)
   No se apaga ninguno -son mediciones reales que Calidad pidio-: se les pone el volumen en
   el nombre para que se distingan en pantalla. El dato ya estaba en su criterio.

QUE NO SE TOCA, porque necesita criterio de Calidad:
   - STBPR02 MAVI-07 "Muestra positiva" x2, con criterios distintos y los dos plausibles
     ("#1, #2, #3 y #4" contra "#1-4 y/o #5 patron PRB-01"). Hay que saber cual vale.
   - El renglon de volumen que tiene el criterio vacio.
   - Los 25 rangos en 0-0 y los 21 bloques sin especificacion, preguntados el 23-sep.

Idempotente.
"""
from collections import defaultdict

Rel = env['amunet.quality.parameter.product.rel'].sudo()
Cfg = env['amunet.quality.parameter.specification.config'].sudo()

# Lo que necesita criterio de Calidad y por eso queda fuera
FUERA = {('STBPR02', 'MAVI-07')}

def normaliza(t):
    return (t or '').strip().rstrip('.').lower()

print('=== 1) el sobrante de cada renglon repetido ===')
apagados = 0
pobres = []
tocados = set()
for rel in Rel.search([('active', '=', True)]):
    clave = rel.product_tmpl_id.default_code or '?'
    if (clave, rel.parameter_id.code) in FUERA:
        continue
    por_nombre = defaultdict(list)
    for c in Cfg.search([('product_parameter_rel_id', '=', rel.id), ('active', '=', True)],
                        order='sequence, id'):
        por_nombre[normaliza(c.specification_name or c.specification_id.name)].append(c)
    for nombre, cfgs in por_nombre.items():
        if len(cfgs) < 2:
            continue
        # el volumen con siete mediciones no es un duplicado: se trata abajo
        if len(cfgs) > 2:
            continue
        # se conserva la que tiene un criterio REAL: ni vacio ni igual al nombre
        def puntua(c):
            crit = normaliza(c.acceptance_criteria)
            if not crit:
                return 0          # criterio vacio: la peor
            if crit == nombre:
                return 1          # el criterio repite el nombre: no dice nada
            return 2              # criterio de verdad
        mejor = max(cfgs, key=lambda c: (puntua(c), -c.id))
        # El renglon que se queda hereda la MEJOR POSICION de los dos. Sin esto, al
        # conservar el del criterio bueno se conserva tambien su secuencia, y varios
        # de esos estan en 99 -- la convencion de "fuera de la lista"-, asi que el
        # renglon correcto acabaria hasta el final de la pantalla.
        seq_visible = min(c.sequence for c in cfgs if c.sequence and c.sequence < 99) \
            if any(c.sequence and c.sequence < 99 for c in cfgs) else mejor.sequence
        for c in cfgs:
            if c == mejor:
                continue
            c.write({'active': False})
            apagados += 1
            tocados.add(rel.id)
            print('   %-10s %-10s "%s"' % (clave, rel.parameter_id.code, nombre[:28]))
            print('        se apaga cfg %-6s seq %-4s criterio="%s"' % (
                c.id, c.sequence, (c.acceptance_criteria or '(vacio)')[:34]))
            print('        se queda cfg %-6s seq %-4s criterio="%s"' % (
                mejor.id, mejor.sequence, (mejor.acceptance_criteria or '(vacio)')[:34]))
        if mejor.sequence != seq_visible:
            print('        (se mueve a la posicion %s, venia en %s)' % (seq_visible, mejor.sequence))
            mejor.write({'sequence': seq_visible})
        if puntua(mejor) < 2:
            pobres.append((clave, rel.parameter_id.code, nombre, mejor.id,
                           mejor.acceptance_criteria or ''))
print('   renglones apagados: %d' % apagados)
if pobres:
    print()
    print('   OJO: estos quedaron activos pero con criterio pobre -- vacio o repitiendo')
    print('   el nombre del renglon. NO se les invento un criterio: lo define Calidad.')
    for clave, code, nombre, cid, crit in pobres:
        print('      %-10s %-10s "%s"  cfg %s  criterio="%s"' % (
            clave, code, nombre[:26], cid, crit or '(vacio)'))

print('\n=== 2) los volumenes, con su medida en el nombre ===')
renombrados = 0
for rel in Rel.search([('active', '=', True), ('parameter_id.code', '=', 'MGA 0981')]):
    clave = rel.product_tmpl_id.default_code or '?'
    cfgs = Cfg.search([('product_parameter_rel_id', '=', rel.id), ('active', '=', True)],
                      order='sequence, id')
    vol = cfgs.filtered(lambda c: normaliza(c.specification_name or c.specification_id.name)
                        == 'variación de volumen')
    if len(vol) < 2:
        continue
    print('   --- %s: %d renglones de volumen' % (clave, len(vol)))
    for c in vol:
        crit = (c.acceptance_criteria or '').strip()
        if not crit:
            print('        cfg %-6s SIN criterio: se deja como esta, lo define Calidad' % c.id)
            continue
        # el criterio trae la medida; se limpia el prefijo que no aporta
        medida = crit.lstrip('µ').strip().lstrip('~').strip()
        nuevo = 'Variación de volumen — %s' % medida
        if (c.specification_name or '') == nuevo:
            print('        cfg %-6s ya dice "%s"' % (c.id, nuevo)); continue
        c.write({'specification_name': nuevo})
        renombrados += 1
        print('        cfg %-6s -> "%s"' % (c.id, nuevo))
print('   renglones renombrados: %d' % renombrados)

print('\n=== 2b) el orden en pantalla: renumerar los bloques descuadrados ===')
# Al quedar un solo renglon de cada par, varios bloques se quedaron con TODAS sus
# secuencias iguales (tres en 10) o en 99, que es la convencion de "fuera de la lista".
# Con eso el orden en pantalla lo decide el id y es impredecible: el analista ve los
# renglones en un orden distinto en cada producto. Se renumeran 10, 20, 30 respetando
# el orden que ya tenian.
ORDEN_MAVI04 = ['manchas y/o suciedad', 'rasgaduras', 'deformidad o deterioro',
                'letra adecuada', 'sellado', 'polvo']
# SOLO los bloques donde este script apago un renglon. En produccion hay 1,017 bloques
# con el orden descuadrado, y reordenarlos todos cambiaria el orden de captura de casi
# todos los analisis: ese orden puede estar atado a los formatos en papel de Calidad, asi
# que no se toca por iniciativa nuestra. Aqui solo se arregla lo que ensuciamos al quitar
# el duplicado -- si el par estaba en seq 10 y 10, el que queda se queda solo en 10 y el
# bloque pierde su orden.
renumerados = 0
for rel in Rel.browse(sorted(tocados)):
    act = Cfg.search([('product_parameter_rel_id', '=', rel.id), ('active', '=', True)],
                     order='sequence, id')
    if len(act) < 2:
        continue
    seqs = [c.sequence for c in act]
    descuadrado = len(set(seqs)) != len(seqs) or all(x == 99 for x in seqs)
    if not descuadrado:
        continue
    # MAVI-04 lleva el orden que usa el resto de la casa; los demas conservan el suyo
    if rel.parameter_id.code == 'MAVI-04':
        def pos(c):
            n = normaliza(c.specification_name or c.specification_id.name)
            return (ORDEN_MAVI04.index(n) if n in ORDEN_MAVI04 else len(ORDEN_MAVI04), c.id)
        ordenados = sorted(act, key=pos)
    else:
        ordenados = list(act)
    print('   %-10s %-10s %d renglones, venian en %s' % (
        rel.product_tmpl_id.default_code or '?', rel.parameter_id.code, len(act), seqs))
    for i, c in enumerate(ordenados, start=1):
        nuevo = i * 10
        if c.sequence != nuevo:
            c.write({'sequence': nuevo})
            renumerados += 1
        print('        %-4s %s' % (nuevo, (c.specification_name or c.specification_id.name)[:46]))
print('   renglones renumerados: %d' % renumerados)

print('\n=== 3) MPAGE03: el punto de calidad que no disparaba nada ===')
t = env['product.template'].sudo().search([('default_code', '=', 'MPAGE03')], limit=1)
if not t:
    print('   no existe MPAGE03')
else:
    puntos = env['amunet.quality.point'].sudo().search([]).filtered(
        lambda q: t.id in q.product_ids.mapped('product_tmpl_id').ids)
    print('   %s "%s"' % (t.default_code, (t.name or '')[:44]))
    print('   puntos de calidad que lo incluyen: %s' % (
        ', '.join(p.name or p.display_name for p in puntos) or 'ninguno'))
    print('   qc_required antes: %s   requiere analisis al producir: %s' % (
        t.qc_required, getattr(t, 'amunet_req_quality_control', '?')))
    if puntos and not t.qc_required:
        t.write({'qc_required': True})
        print('   [ok] qc_required encendido: el punto ya dispara el analisis al recibir')
    elif t.qc_required:
        print('   [ya] estaba encendido')

print('\n=== como queda: quedan renglones repetidos? ===')
quedan = 0
for rel in Rel.search([('active', '=', True)]):
    por_nombre = defaultdict(int)
    for c in Cfg.search([('product_parameter_rel_id', '=', rel.id), ('active', '=', True)]):
        por_nombre[normaliza(c.specification_name or c.specification_id.name)] += 1
    for nombre, n in por_nombre.items():
        if n > 1:
            quedan += 1
            print('   %-10s %-10s "%s" x%d' % (
                rel.product_tmpl_id.default_code or '?', rel.parameter_id.code, nombre[:26], n))
print('   bloques con renglones repetidos: %d  (los que quedan esperan criterio de Calidad)' % quedan)
env.cr.commit()
