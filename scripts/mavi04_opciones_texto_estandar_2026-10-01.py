# -*- coding: utf-8 -*-
"""MAVI-04: poner a las OPCIONES el texto que el analista puede leer.

EL PROBLEMA. Ayer se normalizo el CRITERIO de los renglones de Aspectos, pero no las dos
OPCIONES que el analista elige al capturar. En 12 hojas quedaron asi:

    criterio: Sin manchas y/o suciedad          <- bien
    opciones: "Seleccion Sin"  /  "Con"         <- esto es lo que ve al capturar

Con tres renglones seguidos (Manchas, Rasgaduras, Deformidad), las tres parejas de
opciones se ven IDENTICAS: el analista elige entre "Seleccion Sin" y "Con" sin que la
pantalla diga de que criterio habla, y asi queda impreso en el analisis. En STGEL02 era
un "Sin" suelto, igual de ciego.

Diana lo reviso y autorizo el 01-oct-2026 (respuestas a-e). El texto no se inventa: sale
del nombre del propio renglon, que ya esta bien escrito.

    nucleo   = nombre del renglon en minusculas   ("manchas y/o suciedad")
    criterio = "Sin " + nucleo
    pasa     = "Sin " + nucleo
    falla    = "Con " + nucleo

Es el patron de los 1,523 renglones que ya estaban bien, y coincide exactamente con los
textos que Diana dicto para los criterios que estaban vacios (SPHMC04 Rasgaduras,
SPHMC80 Deformidad, SPHMC34 x2).

LETRA ADECUADA SE DESACTIVA EN SPHMC04 (punto d de Diana): ese criterio aplica a
Producto Terminado, no a hojas maestras. En una hoja maestra, MAVI-04 son solo los tres
estandar. No se borra, se desactiva.

TAMBIEN SE CORRIGEN LOS 5 ANALISIS EN PROCESO (punto e), y hay que hacerlo aparte porque
el renglon del analisis COPIA el texto al crearse: arreglar el catalogo no arregla los
analisis ya abiertos. Son QC/2026/00503, 00504, 00505, 00510 y 00513. Diana los firma en
cuanto queden; el de STGEL02 es urgente porque Almacen espera para liberar el lote.

SEGURO DE HACER: se comprobo que NINGUNO de los 15 renglones tiene resultado capturado
todavia, asi que no hay captura que quede inconsistente con las opciones nuevas. Si
alguno tuviera resultado, el script lo salta y lo reporta.

NO SE TOCAN los renglones numericos ni los de tipo vama_multi_check (Tiempo de
congelacion, Grosor, Ancho, Largo, Muestra negativa/positiva): ahi las opciones binarias
vacias son lo correcto.

Idempotente: solo escribe lo que no coincide.
"""

def textos(nombre):
    """Del nombre del renglon salen los tres textos. Nada se inventa."""
    nucleo = (nombre or '').strip()
    nucleo = nucleo[0].lower() + nucleo[1:] if nucleo else ''
    return 'Sin %s' % nucleo, 'Sin %s' % nucleo, 'Con %s' % nucleo


def malo(pasa, falla):
    pasa, falla = (pasa or ''), (falla or '')
    return (not pasa or not falla or pasa.startswith('Selección')
            or pasa.strip() == 'Sin' or falla.strip() == 'Con')


# ---------- 1) el catalogo ----------
specs = env['amunet.quality.parameter.specification.config'].search([
    ('active', '=', True),
    ('evaluation_type', '=', 'binary_selection'),
    ('product_parameter_rel_id.active', '=', True),
    ('product_parameter_rel_id.parameter_id.code', '=', 'MAVI-04'),
])
specs = specs.filtered(lambda s: s.product_parameter_rel_id.product_tmpl_id.active)
print('renglones MAVI-04 binarios en fichas activas: %s' % len(specs))

# punto d: Letra adecuada no aplica a hojas maestras
letra = specs.filtered(
    lambda s: 'letra' in (s.specification_name or '').lower()
    and s.product_parameter_rel_id.product_tmpl_id.default_code == 'SPHMC04')
for s in letra:
    print('\n[d] SPHMC04 "%s": se DESACTIVA (criterio de Producto Terminado, no de hoja maestra)'
          % s.specification_name)
    s.active = False
specs -= letra

corregidos = []
for s in specs.filtered(lambda x: malo(x.binary_option_pass, x.binary_option_fail)):
    clave = s.product_parameter_rel_id.product_tmpl_id.default_code
    crit, pasa, falla = textos(s.specification_name)
    vals = {'binary_option_pass': pasa, 'binary_option_fail': falla}
    if (s.acceptance_criteria or '').strip().rstrip('.') != crit:
        vals['acceptance_criteria'] = crit
    antes = '%s / %s' % (s.binary_option_pass or '(vacio)', s.binary_option_fail or '(vacio)')
    s.write(vals)
    corregidos.append((clave, s.specification_name, antes, '%s / %s' % (pasa, falla)))

env.cr.commit()
print('\n=== CATALOGO: %s renglon(es) corregido(s) ===' % len(corregidos))
for clave, nombre, antes, ahora in sorted(corregidos):
    print('  %-9s %-24s  %-26s ->  %s' % (clave, nombre[:24], antes[:26], ahora))

# ---------- 2) los 5 analisis en proceso ----------
FOLIOS = ['QC/2026/00503', 'QC/2026/00504', 'QC/2026/00505', 'QC/2026/00510', 'QC/2026/00513']
checks = env['amunet.quality.check'].search([('name', 'in', FOLIOS)])
print('\n=== LOS %s ANALISIS EN PROCESO ===' % len(checks))

tocados, saltados = [], []
for c in checks.sorted('name'):
    dets = c.test_line_ids.mapped("detail_line_ids") if hasattr(c, 'test_line_ids') else env['amunet.quality.test.line.detail']
    for d in dets:
        cfg = d.specification_config_id
        if not cfg or cfg.evaluation_type != 'binary_selection':
            continue
        if (cfg.product_parameter_rel_id.parameter_id.code or '') != 'MAVI-04':
            continue
        if not malo(d.binary_option_pass, d.binary_option_fail):
            continue
        if d.result_binary_option:
            saltados.append((c.name, d.name, d.result_binary_option))
            continue
        crit, pasa, falla = textos(d.name)
        vals = {'binary_option_pass': pasa, 'binary_option_fail': falla}
        if (d.acceptance_criteria or '').strip().rstrip('.') != crit:
            vals['acceptance_criteria'] = crit
        antes = '%s / %s' % (d.binary_option_pass or '(vacio)', d.binary_option_fail or '(vacio)')
        d.write(vals)
        tocados.append((c.name, d.name, antes, '%s / %s' % (pasa, falla)))

env.cr.commit()
for folio, nombre, antes, ahora in tocados:
    print('  %-14s %-24s  %-16s ->  %s' % (folio, nombre[:24], antes[:16], ahora))
if saltados:
    print('\n  SALTADOS por tener resultado ya capturado (revisar a mano):')
    for folio, nombre, res in saltados:
        print('     %-14s %-24s capturado=%s' % (folio, nombre[:24], res))

# ---------- 3) comprobacion ----------
print('\n=== COMPROBACION ===')
quedan = env['amunet.quality.parameter.specification.config'].search([
    ('active', '=', True), ('evaluation_type', '=', 'binary_selection'),
    ('product_parameter_rel_id.active', '=', True),
    ('product_parameter_rel_id.parameter_id.code', '=', 'MAVI-04'),
]).filtered(lambda s: s.product_parameter_rel_id.product_tmpl_id.active
            and malo(s.binary_option_pass, s.binary_option_fail))
print('  catalogo: renglones que siguen mal = %s' % len(quedan))
for s in quedan:
    print('     %-9s %-24s %s / %s' % (
        s.product_parameter_rel_id.product_tmpl_id.default_code, s.specification_name,
        s.binary_option_pass, s.binary_option_fail))

print('\n  los 5 analisis, renglones de MAVI-04:')
for c in checks.sorted('name'):
    for d in c.test_line_ids.mapped("detail_line_ids"):
        cfg = d.specification_config_id
        if cfg and cfg.evaluation_type == 'binary_selection' and \
           (cfg.product_parameter_rel_id.parameter_id.code or '') == 'MAVI-04':
            print('     %-14s %-24s pasa="%s"  falla="%s"' % (
                c.name, d.name[:24], d.binary_option_pass, d.binary_option_fail))

print('\n  SPHMC04 Letra adecuada activa: %s' % env[
    'amunet.quality.parameter.specification.config'].search_count([
        ('active', '=', True), ('specification_name', 'ilike', 'letra'),
        ('product_parameter_rel_id.parameter_id.code', '=', 'MAVI-04'),
        ('product_parameter_rel_id.product_tmpl_id.default_code', '=', 'SPHMC04')]))
