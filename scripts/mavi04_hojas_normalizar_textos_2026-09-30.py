"""Normaliza MAVI-04 en las hojas: 3 renglones, con el texto estandar de la casa.

Aprobado por Diana el 30-sep-2026 (msg 20:46 "APROBADO para subir a produccion") y
autorizado por Mery.

QUE SE HACE, los cuatro puntos que aprobo Diana:

 1. Las hojas quedan con los 3 renglones estandar de MAVI-04: Manchas y/o suciedad,
    Rasgaduras, Deformidad o deterioro. Lo que sobra se DESACTIVA, no se borra.
 2. SPHMC34 baja de 5 a 3: se apagan Polvo y Letra adecuada, que son de la familia vieja
    (Diana, msg 20:47: "mismo criterio que el resto de las hojas").
 3. STBPR02 MAVI-07 "Muestra positiva" se queda con el criterio '#1-4 y/o #5 (patron
    PRB-01...)' y se apaga el otro ('#1, #2, #3 y #4'). Lectura: positivo = patron del #1
    al #4 visible, negativo = patron #5.
 4. Los 1,017 bloques con secuencias descuadradas NO se tocan. Diana: "lo dejamos
    pendiente para revisarlo con calma".

EL TEXTO: SE USA EL ESTANDAR DE LA CASA, NO EL DE SU "CONFIRMACION FINAL".

Diana mando tres versiones del texto en hora y media. La ultima (22:03) decia estar
verificada contra SPHMC85 y pedia mayusculas iniciales y punto final:
"Sin Manchas y/o suciedad" / "Con Deformidad o deterioro.".

Fuimos a ver SPHMC85 en la base y dice otra cosa:

    prefijo       "Seleccion Sin/Con"
    opcion pasa   "Seleccion Sin"
    opcion falla  "Con"
    criterio      "Sin manchas y/o suciedad"      <- minuscula, sin punto

O sea que leyeron el campo equivocado: el texto completo vive en el CRITERIO, no en las
opciones binarias. Y el estandar de la casa es inequivoco -- los 104 productos terminados,
sin una sola excepcion:

    "Sin manchas y/o suciedad" | "Con manchas y/o suciedad"
    "Sin rasgaduras"           | "Con rasgaduras"

Todo en minuscula y sin punto. Eso coincide con su CORRECCION de las 21:52 y no con la
confirmacion de las 22:03. Se aplica ese: asi las hojas quedan iguales al resto del
sistema en vez de introducir una variante con mayusculas intermedias que habria que
mantener aparte. Se le explica en el mensaje de cierre.

Idempotente.
"""
Rel = env['amunet.quality.parameter.product.rel'].sudo()
Cfg = env['amunet.quality.parameter.specification.config'].sudo()
RelX = Rel.with_context(active_test=False)
CfgX = Cfg.with_context(active_test=False)

# el texto estandar, tal como lo tienen los 104 productos terminados
ESTANDAR = {
    'manchas y/o suciedad':   ('Sin manchas y/o suciedad', 'Con manchas y/o suciedad'),
    'rasgaduras':             ('Sin rasgaduras', 'Con rasgaduras'),
    'deformidad o deterioro': ('Sin deformidad o deterioro', 'Con deformidad o deterioro'),
}
HOJAS = ['SPHMC34', 'SPHMC77', 'SPHMC78', 'SPHMC79',
         'SPHMT07', 'SPHMT08', 'SPHMT09', 'SPHMT10', 'SPHMT11', 'SPHMT12']

def norma(t):
    return (t or '').strip().rstrip('.').lower()

print('=== 1 a 3) las hojas: 3 renglones con el texto estandar ===')
apagados = ajustados = 0
for clave in HOJAS:
    t = env['product.template'].sudo().search([('default_code', '=', clave)], limit=1)
    if not t:
        print('   [ojo] no existe %s' % clave); continue
    cambios = []
    for rel in RelX.search([('product_tmpl_id', '=', t.id),
                            ('parameter_id.code', '=', 'MAVI-04'), ('active', '=', True)]):
        activos = CfgX.search([('product_parameter_rel_id', '=', rel.id), ('active', '=', True)],
                              order='sequence, id')
        # lo que no es de los 3 estandar, fuera
        for c in activos:
            n = norma(c.specification_name or c.specification_id.name)
            if n not in ESTANDAR:
                c.write({'active': False})
                apagados += 1
                cambios.append('-%s' % (c.specification_name or c.specification_id.name))
        # los 3 estandar: texto y orden
        orden = ['manchas y/o suciedad', 'rasgaduras', 'deformidad o deterioro']
        for i, nombre in enumerate(orden, start=1):
            cfgs = CfgX.search([('product_parameter_rel_id', '=', rel.id), ('active', '=', True)]).filtered(
                lambda c: norma(c.specification_name or c.specification_id.name) == nombre)
            if not cfgs:
                continue
            c = cfgs[0]
            pasa, falla = ESTANDAR[nombre]
            vals = {}
            if (c.binary_option_pass or '') != pasa:
                vals['binary_option_pass'] = pasa
            if (c.binary_option_fail or '') != falla:
                vals['binary_option_fail'] = falla
            if (c.acceptance_criteria or '') != pasa:
                vals['acceptance_criteria'] = pasa
            if c.binary_expected_option != 'with_prefix':
                vals['binary_expected_option'] = 'with_prefix'
            if c.sequence != i * 10:
                vals['sequence'] = i * 10
            if vals:
                c.write(vals)
                ajustados += 1
                cambios.append('=%s' % nombre[:18])
    if cambios:
        print('   %-9s %s' % (clave, ', '.join(cambios)))
    else:
        print('   %-9s ya estaba' % clave)
print('   renglones apagados: %d   textos ajustados: %d' % (apagados, ajustados))

print('\n=== 4) STBPR02 MAVI-07: se queda el criterio del patron PRB-01 ===')
t = env['product.template'].sudo().search([('default_code', '=', 'STBPR02')], limit=1)
for rel in RelX.search([('product_tmpl_id', '=', t.id),
                        ('parameter_id.code', '=', 'MAVI-07'), ('active', '=', True)]):
    cfgs = CfgX.search([('product_parameter_rel_id', '=', rel.id), ('active', '=', True)]).filtered(
        lambda c: norma(c.specification_name or c.specification_id.name) == 'muestra positiva')
    if len(cfgs) < 2:
        print('   [ya] queda %d renglon de "Muestra positiva"' % len(cfgs))
    else:
        bueno = cfgs.filtered(lambda c: 'PRB-01' in (c.acceptance_criteria or ''))
        if not bueno:
            print('   [ALTO] ninguno tiene el criterio del patron PRB-01; no se toca')
        else:
            for c in cfgs - bueno[0]:
                c.write({'active': False})
                print('   [ok] apagado cfg %s  criterio="%s"' % (c.id, (c.acceptance_criteria or '')[:40]))
            print('   [ok] se queda cfg %s  criterio="%s"' % (bueno[0].id, (bueno[0].acceptance_criteria or '')[:48]))

print('\n=== como queda cada hoja ===')
for clave in HOJAS + ['STBPR02']:
    t = env['product.template'].sudo().search([('default_code', '=', clave)], limit=1)
    if not t: continue
    for rel in RelX.search([('product_tmpl_id', '=', t.id), ('active', '=', True)]):
        if rel.parameter_id.code not in ('MAVI-04', 'MAVI-07'):
            continue
        act = Cfg.search([('product_parameter_rel_id', '=', rel.id), ('active', '=', True)],
                         order='sequence, id')
        if not act:
            continue
        print('   %-9s %-9s %d: %s' % (clave, rel.parameter_id.code, len(act),
              ' | '.join('%s [%s]' % (c.specification_name or c.specification_id.name,
                                      (c.acceptance_criteria or '')[:26]) for c in act)))
env.cr.commit()
