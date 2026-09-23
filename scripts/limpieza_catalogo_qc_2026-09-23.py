# Dos limpiezas del catalogo de Calidad, autorizadas por Mery el 23-sep-2026
# a partir del chequeo diario de configuracion.
#
# 1. El bloque 29 (RES-01 Resistencia Sellado) cuelga del producto id 1673
#    'Bolsas Termosellables', que esta ARCHIVADO y sin clave. Nunca se uso en
#    ningun analisis. Se desactiva.
#
# 2. Dos nombres de especificacion con errata de captura. Salen impresos en los
#    analisis. Corregirlos no altera los analisis ya cerrados: esos guardan su
#    propia copia del texto en la linea de detalle.
ERRATAS = {
    104: ('Obtención de al menos 5 gotas co n promedio de gota',
          'Obtención de al menos 5 gotas con promedio de gota'),
    400: ('Liberacin de muestra  a 2 min.',
          'Liberación de muestra a 2 min.'),
}

Rel = env['amunet.quality.parameter.product.rel']
Spec = env['amunet.quality.check.parameter.specification']

# --- 1. el bloque huerfano ---
r = Rel.browse(29)
assert r.exists(), 'No existe el bloque 29'
assert not r.product_tmpl_id.active, 'El producto del bloque 29 esta ACTIVO, no se toca'
usos = env['amunet.quality.parameter.specification.config'].search_count(
    [('product_parameter_rel_id', '=', 29)])
assert usos == 0, 'El bloque 29 tiene %s configuraciones, no se toca' % usos
if r.active:
    r.active = False
    print('bloque 29 desactivado (%s, producto archivado %r)'
          % (r.parameter_code, r.product_tmpl_id.name))
else:
    print('bloque 29 ya estaba desactivado')

# --- 2. las erratas ---
for sid, (viejo, nuevo) in ERRATAS.items():
    s = Spec.with_context(active_test=False).browse(sid)
    if not s.exists():
        print('  spec %s no existe' % sid); continue
    actual = s.name or ''
    if actual == nuevo:
        print('  spec %-4s ya estaba corregida' % sid); continue
    if actual != viejo:
        print('  spec %-4s NO coincide con lo esperado, se deja: %r' % (sid, actual[:50])); continue
    # se escribe en los dos idiomas: si solo se toca en_US, el usuario en es_MX
    # sigue viendo el texto viejo cuando ya existe una traduccion propia.
    s.with_context(lang='en_US').name = nuevo
    s.with_context(lang='es_MX').name = nuevo
    print('  spec %-4s %r -> %r' % (sid, viejo[:44], nuevo[:44]))

env.cr.commit()
print('\n--- verificacion ---')
print('  bloques activos sin especificacion: %s' % len([
    x for x in Rel.search([('active', '=', True)])
    if env['amunet.quality.parameter.specification.config'].search_count(
        [('product_parameter_rel_id', '=', x.id), ('active', '=', True)]) == 0]))
for sid in ERRATAS:
    s = Spec.with_context(active_test=False).browse(sid)
    print('  spec %-4s es_MX=%r' % (sid, s.with_context(lang='es_MX').name))
