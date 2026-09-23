"""Opciones binarias vacias en renglones de analisis - version ORM.

Mismo objetivo que fix_binary_options_analisis_abiertos_prod.py (Diana,
23-sep-2026): los renglones de seleccion binaria guardan su PROPIA copia del
texto "aprobado / rechazado". Cuando esa copia quedo vacia, la pantalla no
puede pintar los botones y el analisis no se deja cerrar.

Se reescribio con la ORM porque el original hacia UPDATE directo a las tablas.
Estos son registros de calidad ISO 13485: un UPDATE se salta las validaciones,
el chatter y el tracking, y deja el dato sin rastro de quien lo cambio.

Excluido detail_id 3205 (SPHMC04, tiempo de migracion): su configuracion
tambien esta vacia, no hay de donde copiar. Requiere criterio de Diana.

Idempotente. Reporta QUE producto toco, no solo cuantos renglones.
"""

Detail = env['amunet.quality.test.line.detail']
Config = env['amunet.quality.parameter.specification.config']
Rel    = env['amunet.quality.parameter.product.rel']

EXCLUIDOS = (3205,)

vacios = Detail.search([
    ('evaluation_type', '=', 'binary_selection'),
    '|', ('binary_option_pass', 'in', [False, '']),
         ('binary_option_fail', 'in', [False, '']),
])
vacios = vacios.filtered(lambda d: d.id not in EXCLUIDOS)
print('Renglones vacios encontrados: %s' % len(vacios))

corregidos = {}
sin_fuente = []

for d in vacios:
    tl = d.test_line_id
    qc = tl.check_id
    tmpl = qc.product_id.product_tmpl_id
    if not tmpl or not tl.code:
        sin_fuente.append((d.id, '?', d.name, 'sin producto o sin codigo de parametro'))
        continue
    # TODOS los bloques, no el primero: un producto puede tener varios rel
    # con el mismo codigo de parametro (duplicados historicos), y la config
    # buena vive en cualquiera de ellos.
    rels = Rel.search([('product_tmpl_id', '=', tmpl.id),
                       ('parameter_code', '=', tl.code)])
    if not rels:
        sin_fuente.append((d.id, tmpl.default_code, d.name, 'el producto no tiene ese parametro configurado'))
        continue
    cfg = Config.search([
        ('product_parameter_rel_id', 'in', rels.ids),
        ('specification_name', '=', d.name),
        ('active', '=', True),
        ('binary_option_pass', 'not in', [False, '']),
        ('binary_option_fail', 'not in', [False, '']),
    ], limit=1)
    if not cfg:
        sin_fuente.append((d.id, tmpl.default_code, d.name, 'ninguna configuracion del producto tiene ese renglon con opciones'))
        continue
    d.write({'binary_option_pass': cfg.binary_option_pass,
             'binary_option_fail': cfg.binary_option_fail})
    corregidos.setdefault(tmpl.default_code, []).append(d.name)

print('\n--- CORREGIDOS por producto ---')
total = 0
for code in sorted(corregidos):
    nombres = corregidos[code]
    total += len(nombres)
    print('  %-9s %2d renglones: %s' % (code, len(nombres), ', '.join(sorted(set(nombres)))[:70]))
print('  TOTAL: %s renglones en %s productos' % (total, len(corregidos)))

if sin_fuente:
    print('\n--- SIN CORREGIR (no hay de donde copiar) ---')
    for det_id, code, nombre, motivo in sin_fuente:
        print('  detail %-6s %-9s %-32s %s' % (det_id, code, nombre[:32], motivo))

env.cr.commit()
print('\nOK: cambios guardados.')
