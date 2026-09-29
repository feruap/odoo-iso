"""MAVI-04 de Producto Terminado: deja los 98 productos con el esquema de 8 renglones.

Respuestas de Diana del 29-sep-2026 (msg 19:46) a las tres preguntas del 21-sep, y
autorizado por Mery.

    1. Sellado: SI va en todos los PT, no solo en los de sobre sellado.
    2. Polvo y Manchas: SI van en todos, en la seccion de empaque.
    3. Los 4 con dos bloques MAVI-04: los dos son correctos y se quedan.

EL ESQUEMA DE 8 que definio Diana:
    10  Polvo
    20  Manchas y/o suciedad
    30  Rasgaduras - Empaque
    40  Deformidad o deterioro - Empaque
    50  Sellado                             <- el que falta en casi todos
    60  Rasgaduras - Prueba
    70  Deformidad o deterioro - Prueba
    80  Letra adecuada - Empaque

Sellado va en 50, aprovechando el hueco que ya existia entre Deformidad-Empaque (40) y
Rasgaduras-Prueba (60): es un aspecto de empaque y ahi cierra ese bloque.

OJO CON EL PARAMETRO: hay CUATRO parametros distintos con el codigo MAVI-04, y no son
duplicados, son ambitos distintos con el mismo codigo:
    id 1   "Aspectos"                        293 relaciones (materia prima, hojas)
    id 113 "Aspectos Estructura del hisopo"    6
    id 114 "Aspectos Apariencia del empaque"   6
    id 145 "Aspectos Visuales"               104 relaciones (PRODUCTO TERMINADO)
Este script toca SOLO "Aspectos Visuales". Buscar por codigo con limit=1 agarra el id 1 y
toca materias primas: por eso aqui se busca por NOMBRE, no por codigo ni por id.

TODO SE BUSCA POR NOMBRE, NUNCA POR ID, porque los ids de especificacion NO coinciden
entre staging y produccion. Ya paso con los bloques 4695/4785 que Calidad reporto en
septiembre.

QUE HACE, medido contra produccion el 29-sep:
    85 productos ya tienen los 7 correctos  ->  se les agrega Sellado
    13 productos tienen Rasgaduras y Deformidad SIN desdoblar
                                            ->  se desdoblan en Empaque/Prueba y se
                                                les agrega Sellado
     6 productos estan ARCHIVADOS (Lactoferrina, Filariasis, Brucella, Lyme,
       Clostridium, Fentanilo, con claves de proveedor)  ->  NO se tocan

SIN EFECTO EN LO YA CAPTURADO: los renglones de un analisis se copian al crearlo, asi que
esto solo cambia los analisis NUEVOS. Hay 1 analisis abierto de estos productos
(QC/2026/00490, DMCRD01) y conserva sus renglones.

Los genericos que se desdoblan se DESACTIVAN, no se borran: un renglon borrado del
catalogo rompe el historico de cualquier analisis que lo haya usado.

Idempotente.
"""
Rel = env['amunet.quality.parameter.product.rel'].sudo()
Cfg = env['amunet.quality.parameter.specification.config'].sudo()
CfgX = Cfg.with_context(active_test=False)
P = env['amunet.quality.check.parameter'].sudo()

param = P.search([('code', '=', 'MAVI-04'), ('name', 'ilike', 'Aspectos Visuales')], limit=1)
assert param, 'no se encontro el parametro MAVI-04 "Aspectos Visuales"'
print('parametro: id %s  "%s"  (%d especificaciones en catalogo)' % (
    param.id, param.name, len(param.specification_line_ids)))

def spec(nombre):
    """La especificacion del catalogo de ESTE parametro, por nombre exacto."""
    s = param.specification_line_ids.filtered(lambda x: (x.name or '').strip() == nombre)
    assert len(s) == 1, 'se esperaba una sola especificacion "%s", hay %d' % (nombre, len(s))
    return s

ESQUEMA = [
    (10, 'Polvo'),
    (20, 'Manchas y/o suciedad'),
    (30, 'Rasgaduras — Empaque'),
    (40, 'Deformidad o deterioro — Empaque'),
    (50, 'Sellado'),
    (60, 'Rasgaduras — Prueba'),
    (70, 'Deformidad o deterioro — Prueba'),
    (80, 'Letra adecuada — Empaque'),
]
GENERICOS = ['Rasgaduras', 'Deformidad o deterioro']   # los que se desdoblan

# ---- de donde se copia la configuracion de cada renglon -------------------
# se toma de un producto que YA lo tenga bien configurado en esta misma base
modelos = {}
for _seq, nombre in ESQUEMA:
    s = spec(nombre)
    m = CfgX.search([('specification_id', '=', s.id), ('active', '=', True)], limit=1)
    if not m:
        m = CfgX.search([('specification_id', '=', s.id)], limit=1)
    assert m, 'no hay ningun producto de donde copiar la configuracion de "%s"' % nombre
    modelos[nombre] = m
    print('   "%-34s" se copia de %s' % (nombre, m.product_tmpl_id.default_code or m.product_tmpl_id.id))

EXCLUIR = {'id', 'product_parameter_rel_id', 'product_tmpl_id', 'parameter_id',
           'company_id', 'create_uid', 'create_date', 'write_uid', 'write_date',
           'display_name', '__last_update', 'specification_id', 'sequence', 'active'}
COPIABLES = [n for n, f in Cfg._fields.items()
             if f.store and not f.related and not f.compute and n not in EXCLUIR]

def valores_de(modelo):
    v = {}
    for n in COPIABLES:
        f = Cfg._fields[n]
        val = modelo[n]
        if f.type == 'many2one':
            v[n] = val.id or False
        elif f.type in ('one2many', 'many2many'):
            v[n] = [(6, 0, val.ids)]
        else:
            v[n] = val
    return v

print()
agregados = activados = desactivados = ya_estaban = 0
saltados = []
for rel in Rel.search([('parameter_id', '=', param.id), ('active', '=', True)],
                      order='id'):
    tmpl = rel.product_tmpl_id
    if not tmpl.active:
        saltados.append(tmpl.default_code or str(tmpl.id))
        continue
    cambios = []
    for seq, nombre in ESQUEMA:
        s = spec(nombre)
        cfg = CfgX.search([('product_parameter_rel_id', '=', rel.id),
                           ('specification_id', '=', s.id)], limit=1)
        if cfg:
            if not cfg.active:
                cfg.write({'active': True, 'sequence': seq})
                cambios.append('+%s (reactivado)' % nombre)
                activados += 1
            else:
                if cfg.sequence != seq:
                    cfg.write({'sequence': seq})
                ya_estaban += 1
        else:
            vals = valores_de(modelos[nombre])
            vals.update({'product_parameter_rel_id': rel.id,
                         'specification_id': s.id, 'sequence': seq, 'active': True})
            Cfg.create(vals)
            cambios.append('+%s' % nombre)
            agregados += 1
    # los genericos sin desdoblar salen de escena
    for nombre in GENERICOS:
        s = spec(nombre)
        cfg = CfgX.search([('product_parameter_rel_id', '=', rel.id),
                           ('specification_id', '=', s.id), ('active', '=', True)], limit=1)
        if cfg:
            cfg.write({'active': False})
            cambios.append('-%s (desdoblado en Empaque y Prueba)' % nombre)
            desactivados += 1
    if cambios:
        print('   %-12s %s' % (tmpl.default_code or tmpl.id, ', '.join(cambios)))

print()
print('   renglones agregados:     %d' % agregados)
print('   renglones reactivados:   %d' % activados)
print('   genericos desactivados:  %d' % desactivados)
print('   ya estaban bien:         %d' % ya_estaban)
print('   productos archivados que no se tocaron: %d  %s' % (len(saltados), saltados))

print('\n=== como queda: cuantos renglones tiene cada producto ===')
from collections import Counter
cuenta = Counter()
for rel in Rel.search([('parameter_id', '=', param.id), ('active', '=', True)]):
    if not rel.product_tmpl_id.active:
        continue
    n = Cfg.search_count([('product_parameter_rel_id', '=', rel.id), ('active', '=', True)])
    cuenta[n] += 1
for n, cuantos in sorted(cuenta.items()):
    print('   %3d productos con %d renglones' % (cuantos, n))
env.cr.commit()
