"""STGEL02 (Gel refrigerante BRICK): configura su calidad y destraba el analisis.

Pedido por Calidad el 29-sep-2026 (script fix_stgel02_configurar_analisis_939.sql v2) y
autorizado por Mery el 30-sep.

EL PROBLEMA: STGEL02 no tenia NINGUN parametro de calidad configurado, y su analisis
QC/2026/00510 (id 939) estaba en proceso con CERO renglones: no habia nada que capturar.
El lote GEL02082601 lleva detenido desde el 19-ago con 10 pz en Control de calidad y 50 en
existencias.

LA ESPECIFICACION es la que definio Calidad segun RAST-047 / CERST-047:

    MAVI-04  Aspectos            3 renglones binarios
             Manchas y/o suciedad, Rasgaduras, Deformidad o deterioro
    MAVI-23  (temperatura)       2 renglones numericos
             Tiempo de congelacion      menos de 24 h        rango 0 a 24
             Mantenimiento de temp.     <=20 C +-2 C, 8 h    rango -30 a 20
    MAVI-11  Dimensiones         3 renglones numericos
             Largo   17 +-1 cm   16 a 18
             Ancho   12 +-1 cm   11 a 13
             Grosor  1.5 +-0.5   1 a 2

POR QUE POR ORM Y NO CON SU SQL. Tres razones concretas, no de forma:

  1. Su INSERT escribe binary_expected_option = 'pass', y ese campo solo admite
     'with_prefix' o 'without_prefix'. Un UPDATE directo no valida los Selection, asi que
     el renglon habria quedado con un valor que la pantalla no sabe mostrar -- el mismo
     defecto que dejo SMP/26/00303 con 'transfer' en vez de 'transferencia'.
  2. Marca todo como create_uid = 1, el bot del sistema. En un registro ISO 13485 eso
     borra quien lo hizo.
  3. Crea los renglones del analisis a mano, sin pasar por el generador del modulo, asi
     que se quedan sin los valores que cada especificacion deriva (prefijos, opciones,
     rangos) y la pantalla de captura sale incompleta.

OJO CON EL AUTOGENERADO: al crear una relacion de parametro, el modulo agrega un renglon
por CADA especificacion del catalogo de ese parametro -- MAVI-11 trae 154, con longitud de
mango y grosor de hisopo. Los que no aplican se DESACTIVAN, no se borran: borrar un renglon
del catalogo rompe el historico de cualquier analisis que lo haya usado.

Todo se busca por NOMBRE, nunca por id: los ids no coinciden entre staging y produccion.

Idempotente.
"""
Param = env['amunet.quality.check.parameter'].sudo()
Spec = env['amunet.quality.check.parameter.specification'].sudo()
Rel = env['amunet.quality.parameter.product.rel'].sudo()
Cfg = env['amunet.quality.parameter.specification.config'].sudo()
RelX = Rel.with_context(active_test=False)
CfgX = Cfg.with_context(active_test=False)

tmpl = env['product.template'].sudo().search([('default_code', '=', 'STGEL02')], limit=1)
assert tmpl, 'no existe STGEL02'
print('STGEL02 = template %s  "%s"' % (tmpl.id, tmpl.name))

def param_exacto(code, nombre):
    """El parametro por codigo Y nombre exacto.

    Hace falta el nombre porque MAVI-04 lo comparten CUATRO parametros distintos, y
    los cuatro empiezan con 'Aspectos': 'Aspectos' (materia prima y semiterminados),
    'Aspectos Estructura del hisopo', 'Aspectos Apariencia del empaque' y 'Aspectos
    Visuales' (producto terminado). Buscar por codigo con limit=1 agarra el que toque.
    """
    ps = Param.search([('code', '=', code)]).filtered(
        lambda p: (p.name or '').strip() == nombre)
    assert len(ps) == 1, 'se esperaba un solo parametro %s "%s", hay %d' % (
        code, nombre, len(ps))
    return ps

# STGEL02 es semiterminado, asi que su MAVI-04 es el de nombre 'Aspectos' pelado
P04 = param_exacto('MAVI-04', 'Aspectos')
P23 = Param.search([('code', '=', 'MAVI-23')], limit=1)
P11 = Param.search([('code', '=', 'MAVI-11')], limit=1)
assert P23 and P11, 'falta MAVI-23 o MAVI-11'
print('   MAVI-04 -> %s "%s"   MAVI-23 -> %s "%s"   MAVI-11 -> %s "%s"' % (
    P04.id, P04.name, P23.id, P23.name, P11.id, P11.name))

# ---- las dos especificaciones de temperatura, si no estan en el catalogo -------
print('\n=== catalogo de MAVI-23: las dos de gel ===')
for nombre in ('Tiempo de congelación', 'Mantenimiento de temperatura'):
    s = P23.specification_line_ids.filtered(lambda x: (x.name or '').strip() == nombre)
    if s:
        print('   [ya] "%s" existe (spec %s)' % (nombre, s[0].id))
    else:
        s = Spec.create({'parameter_id': P23.id, 'name': nombre,
                         'evaluation_type': 'numeric_range'})
        print('   [ok] "%s" creada (spec %s)' % (nombre, s.id))

# ---- el esquema de 8 --------------------------------------------------------
ESQUEMA = [
    (P04, 'Manchas y/o suciedad', 10, {
        'evaluation_type': 'binary_selection',
        'acceptance_criteria': 'Sin manchas y/o suciedad',
        'binary_prefix': 'Sin/Con',
        'binary_option_pass': 'Sin manchas y/o suciedad',
        'binary_option_fail': 'Con manchas y/o suciedad',
        'binary_expected_option': 'with_prefix'}),
    (P04, 'Rasgaduras', 20, {
        'evaluation_type': 'binary_selection',
        'acceptance_criteria': 'Sin rasgaduras',
        'binary_prefix': 'Sin/Con',
        'binary_option_pass': 'Sin rasgaduras',
        'binary_option_fail': 'Con rasgaduras',
        'binary_expected_option': 'with_prefix'}),
    (P04, 'Deformidad o deterioro', 30, {
        'evaluation_type': 'binary_selection',
        'acceptance_criteria': 'Sin deformidad o deterioro',
        'binary_prefix': 'Sin/Con',
        'binary_option_pass': 'Sin deformidad o deterioro',
        'binary_option_fail': 'Con deformidad o deterioro',
        'binary_expected_option': 'with_prefix'}),
    (P23, 'Tiempo de congelación', 10, {
        'evaluation_type': 'numeric_range',
        'acceptance_criteria': 'Menos de 24 horas',
        'min_value': 0.0, 'max_value': 24.0}),
    (P23, 'Mantenimiento de temperatura', 20, {
        'evaluation_type': 'numeric_range',
        'acceptance_criteria': 'Mantiene temperatura ≤20°C ± 2°C durante al menos 8 horas',
        'min_value': -30.0, 'max_value': 20.0}),
    (P11, 'Largo', 10, {
        'evaluation_type': 'numeric_range',
        'acceptance_criteria': '17 ± 1 cm', 'min_value': 16.0, 'max_value': 18.0}),
    (P11, 'Ancho', 20, {
        'evaluation_type': 'numeric_range',
        'acceptance_criteria': '12 ± 1 cm', 'min_value': 11.0, 'max_value': 13.0}),
    (P11, 'Grosor', 30, {
        'evaluation_type': 'numeric_range',
        'acceptance_criteria': '1.5 ± 0.5 cm', 'min_value': 1.0, 'max_value': 2.0}),
]

print('\n=== configurando los 8 renglones ===')
por_param = {}
for P, nombre, seq, vals in ESQUEMA:
    spec = P.specification_line_ids.filtered(lambda x: (x.name or '').strip() == nombre)
    assert len(spec) >= 1, 'no existe "%s" en el catalogo de %s' % (nombre, P.code)
    spec = spec[0]
    rel = RelX.search([('product_tmpl_id', '=', tmpl.id), ('parameter_id', '=', P.id)], limit=1)
    if not rel:
        # el create autogenera un renglon por cada especificacion del catalogo
        rel = Rel.create({'product_tmpl_id': tmpl.id, 'parameter_id': P.id})
        print('   %-9s relacion creada (%s)' % (P.code, rel.id))
    elif not rel.active:
        rel.write({'active': True})
    por_param.setdefault(P.id, (rel, set()))[1].add(spec.id)

    cfg = CfgX.search([('product_parameter_rel_id', '=', rel.id),
                       ('specification_id', '=', spec.id)], limit=1)
    vals = dict(vals, specification_name=nombre, sequence=seq, active=True)
    if cfg:
        cfg.write(vals)
        print('      = %-30s actualizado (cfg %s)' % (nombre[:30], cfg.id))
    else:
        vals.update({'product_parameter_rel_id': rel.id, 'specification_id': spec.id})
        cfg = Cfg.create(vals)
        print('      + %-30s creado (cfg %s)' % (nombre[:30], cfg.id))

# lo que el autogenerado trajo de mas
print('\n=== lo que no aplica a un gel, desactivado ===')
for pid, (rel, buenos) in por_param.items():
    sobra = CfgX.search([('product_parameter_rel_id', '=', rel.id), ('active', '=', True)])
    n = 0
    for c in sobra:
        if c.specification_id.id not in buenos:
            c.write({'active': False}); n += 1
    print('   %-9s %d renglones desactivados' % (Param.browse(pid).code, n))

# ---- el analisis 939 -------------------------------------------------------
print('\n=== el analisis QC/2026/00510 ===')
qc = env['amunet.quality.check'].sudo().search([('name', '=', 'QC/2026/00510')], limit=1)
if not qc:
    print('   [ojo] no se encontro')
else:
    antes = sum(len(l.detail_line_ids) for l in qc.test_line_ids)
    print('   %s  id %s  lote %s  estado %s  renglones antes: %d' % (
        qc.name, qc.id, qc.lot_id.name or '-', qc.state, antes))
    if antes:
        print('   [ya] ya tiene renglones; no se regenera para no borrar captura')
    else:
        qc._load_product_parameters()
        for l in qc.test_line_ids:
            print('      %-9s %d renglones' % (l.parameter_id.code, len(l.detail_line_ids)))
        print('   TOTAL: %d renglones' % sum(len(l.detail_line_ids) for l in qc.test_line_ids))

print('\n=== como queda STGEL02 ===')
for rel in RelX.search([('product_tmpl_id', '=', tmpl.id), ('active', '=', True)]):
    act = Cfg.search([('product_parameter_rel_id', '=', rel.id), ('active', '=', True)], order='sequence,id')
    print('   %-9s %d activos: %s' % (rel.parameter_id.code, len(act),
          ' | '.join('%s [%s]' % (c.specification_name, c.acceptance_criteria or '') for c in act)))
env.cr.commit()
