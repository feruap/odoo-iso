"""
MAVI-07: criterios y mapeo de patrones para cualitativos y competitivos.

Equivalente por ORM del fix_competitivos_mavi07_prod.sql de Calidad
(Diana Flores, 2026-09-22). Se reescribio por dos razones:

  1. El original eran UPDATE directos sobre datos de negocio: sin validacion,
     sin constrains y sin rastro en el chatter. Uno de ellos escribia sobre el
     detalle de un analisis ABIERTO, que es un registro regulado.
  2. El bloque del analisis 910 se pisaba a si mismo: el primer UPDATE dejaba
     'patron #1' en el texto y el segundo filtraba por LIKE '%patron #1%', asi
     que los renglones recien cambiados volvian a entrar y TODOS acababan con
     el texto de la muestra positiva. Aqui se lee antes de escribir.

Solicitado por: Diana Flores - Control de Calidad
"""

Config = env['amunet.quality.parameter.specification.config']
Detail = env['amunet.quality.test.line.detail']

COMPETITIVOS = ['DMADB01', 'DMADO02', 'DMDRO01', 'DMFEN01', 'DRAM-002',
                'DMACT02', 'DMADS01', 'DMAMP02', 'DMMET02', 'DMOPI02', 'DMTHC02']

CUALI_NEG = 'Visualización solo de línea control, patrón #5'
CUALI_NEG_M = '{"positions":[{"type":"select","index":0,"label":"Patrón Observado","options":[{"label":"#1 (Línea T muy intensa)","value":"result_1"},{"label":"#2 (Línea T intensa)","value":"result_2"},{"label":"#3 (Línea T moderada)","value":"result_3"},{"label":"#4 (Línea T tenue)","value":"result_4"},{"label":"#5 (Sin línea T, solo línea C)","value":"result_5"},{"label":"#6 (Sin línea C, con línea T visible)","value":"result_6"},{"label":"#7 (Sin línea C ni línea T)","value":"result_7"},{"label":"N/A (control no disponible)","value":"na"}],"instruction":"Seleccione el patrón visualizado."}],"evaluation":{"rules":[{"result":"result_5","message":"Muestra Negativa: Patrón #5 (sin línea T, solo C) - CUMPLE","verdict":"pass","sample_type":"negative"},{"result":"result_1","message":"Muestra Negativa: Patrón #1 (línea T visible) - NO CUMPLE","verdict":"fail","sample_type":"negative"},{"result":"result_2","message":"Muestra Negativa: Patrón #2 (línea T visible) - NO CUMPLE","verdict":"fail","sample_type":"negative"},{"result":"result_3","message":"Muestra Negativa: Patrón #3 (línea T visible) - NO CUMPLE","verdict":"fail","sample_type":"negative"},{"result":"result_4","message":"Muestra Negativa: Patrón #4 (línea T visible) - NO CUMPLE","verdict":"fail","sample_type":"negative"},{"result":"result_6","message":"Muestra Negativa: Patrón #6 (sin línea C) - Prueba Inválida - RECHAZADO","verdict":"fail","sample_type":"negative"},{"result":"result_7","message":"Muestra Negativa: Patrón #7 (sin línea C ni T) - Prueba Inválida - RECHAZADO","verdict":"fail","sample_type":"negative"},{"result":"na","message":"Muestra Negativa: Control no disponible - N/A","verdict":"not_applicable","sample_type":"negative"}]},"phrase_template":"Muestra negativa: Patrón {0}","fixed_sample_type":"negative"}'
CUALI_POS = 'Visualización línea control y línea de prueba, patrón #1, #2, #3 y #4'
CUALI_POS_M = '{"positions":[{"type":"select","index":0,"label":"Patrón Observado","options":[{"label":"#1 (Línea T muy intensa)","value":"result_1"},{"label":"#2 (Línea T intensa)","value":"result_2"},{"label":"#3 (Línea T moderada)","value":"result_3"},{"label":"#4 (Línea T tenue)","value":"result_4"},{"label":"#5 (Sin línea T, solo línea C)","value":"result_5"},{"label":"#6 (Sin línea C, con línea T visible)","value":"result_6"},{"label":"#7 (Sin línea C ni línea T)","value":"result_7"},{"label":"N/A (control no disponible)","value":"na"}],"instruction":"Seleccione el patrón visualizado."}],"evaluation":{"rules":[{"result":"result_1","message":"Muestra Positiva: Patrón #1 (líneas C+T) - CUMPLE","verdict":"pass","sample_type":"positive"},{"result":"result_2","message":"Muestra Positiva: Patrón #2 (líneas C+T) - CUMPLE","verdict":"pass","sample_type":"positive"},{"result":"result_3","message":"Muestra Positiva: Patrón #3 (líneas C+T) - CUMPLE","verdict":"pass","sample_type":"positive"},{"result":"result_4","message":"Muestra Positiva: Patrón #4 (líneas C+T) - CUMPLE","verdict":"pass","sample_type":"positive"},{"result":"result_5","message":"Muestra Positiva: Patrón #5 (sin línea T) - NO CUMPLE","verdict":"fail","sample_type":"positive"},{"result":"result_6","message":"Muestra Positiva: Patrón #6 (sin línea C) - Prueba Inválida - RECHAZADO","verdict":"fail","sample_type":"positive"},{"result":"result_7","message":"Muestra Positiva: Patrón #7 (sin línea C ni T) - Prueba Inválida - RECHAZADO","verdict":"fail","sample_type":"positive"},{"result":"na","message":"Muestra Positiva: Control no disponible - N/A","verdict":"not_applicable","sample_type":"positive"}]},"phrase_template":"Muestra positiva: Patrón {0}","fixed_sample_type":"positive"}'
COMP_NEG = 'Visualización línea control y línea de prueba, patrón #1, #2, #3 y #4'
COMP_NEG_M = '{"positions":[{"type":"select","index":0,"label":"Patrón Observado","options":[{"label":"#1 (Línea T muy intensa)","value":"result_1"},{"label":"#2 (Línea T intensa)","value":"result_2"},{"label":"#3 (Línea T moderada)","value":"result_3"},{"label":"#4 (Línea T tenue)","value":"result_4"},{"label":"#5 (Sin línea T, solo línea C)","value":"result_5"},{"label":"#6 (Sin línea C, con línea T visible)","value":"result_6"},{"label":"#7 (Sin línea C ni línea T)","value":"result_7"},{"label":"N/A (control no disponible)","value":"na"}],"instruction":"Seleccione el patrón visualizado."}],"evaluation":{"rules":[{"result":"result_1","message":"Muestra Negativa: Patrón #1 (C+T, sin analito) - CUMPLE","verdict":"pass","sample_type":"negative"},{"result":"result_2","message":"Muestra Negativa: Patrón #2 (C+T, sin analito) - CUMPLE","verdict":"pass","sample_type":"negative"},{"result":"result_3","message":"Muestra Negativa: Patrón #3 (C+T, sin analito) - CUMPLE","verdict":"pass","sample_type":"negative"},{"result":"result_4","message":"Muestra Negativa: Patrón #4 (C+T, sin analito) - CUMPLE","verdict":"pass","sample_type":"negative"},{"result":"result_5","message":"Muestra Negativa: Patrón #5 (solo C, analito detectado) - NO CUMPLE","verdict":"fail","sample_type":"negative"},{"result":"result_6","message":"Muestra Negativa: Patrón #6 (sin línea C) - Prueba Inválida - RECHAZADO","verdict":"fail","sample_type":"negative"},{"result":"result_7","message":"Muestra Negativa: Patrón #7 (sin línea C ni T) - Prueba Inválida - RECHAZADO","verdict":"fail","sample_type":"negative"},{"result":"na","message":"Muestra Negativa: Control no disponible - N/A","verdict":"not_applicable","sample_type":"negative"}]},"phrase_template":"Muestra negativa: Patrón {0}","fixed_sample_type":"negative"}'
COMP_POS = 'Visualización solo de línea control, patrón #5'
COMP_POS_M = '{"positions":[{"type":"select","index":0,"label":"Patrón Observado","options":[{"label":"#1 (Línea T muy intensa)","value":"result_1"},{"label":"#2 (Línea T intensa)","value":"result_2"},{"label":"#3 (Línea T moderada)","value":"result_3"},{"label":"#4 (Línea T tenue)","value":"result_4"},{"label":"#5 (Sin línea T, solo línea C)","value":"result_5"},{"label":"#6 (Sin línea C, con línea T visible)","value":"result_6"},{"label":"#7 (Sin línea C ni línea T)","value":"result_7"},{"label":"N/A (control no disponible)","value":"na"}],"instruction":"Seleccione el patrón visualizado."}],"evaluation":{"rules":[{"result":"result_1","message":"Muestra Positiva: Patrón #1 (línea T visible) - NO CUMPLE","verdict":"fail","sample_type":"positive"},{"result":"result_2","message":"Muestra Positiva: Patrón #2 (línea T visible) - NO CUMPLE","verdict":"fail","sample_type":"positive"},{"result":"result_3","message":"Muestra Positiva: Patrón #3 (línea T visible) - NO CUMPLE","verdict":"fail","sample_type":"positive"},{"result":"result_4","message":"Muestra Positiva: Patrón #4 (línea T visible) - NO CUMPLE","verdict":"fail","sample_type":"positive"},{"result":"result_5","message":"Muestra Positiva: Patrón #5 (sin línea T, solo C) - CUMPLE","verdict":"pass","sample_type":"positive"},{"result":"result_6","message":"Muestra Positiva: Patrón #6 (sin línea C) - Prueba Inválida - RECHAZADO","verdict":"fail","sample_type":"positive"},{"result":"result_7","message":"Muestra Positiva: Patrón #7 (sin línea C ni T) - Prueba Inválida - RECHAZADO","verdict":"fail","sample_type":"positive"},{"result":"na","message":"Muestra Positiva: Control no disponible - N/A","verdict":"not_applicable","sample_type":"positive"}]},"phrase_template":"Muestra positiva: Patrón {0}","fixed_sample_type":"positive"}'


def aplicar(spec_name, competitivo, criteria, mapping):
    dom = [('active', '=', True),
           ('parameter_id.code', '=', 'MAVI-07'),
           ('specification_id.name', '=', spec_name),
           ('product_tmpl_id.default_code',
            'in' if competitivo else 'not in', COMPETITIVOS)]
    cfgs = Config.search(dom)
    if not competitivo:
        cfgs = cfgs.filtered(lambda c: (c.product_tmpl_id.default_code or '')
                             .upper().startswith(('DM', 'DL', 'DIAM', 'DRAM', 'DEMAM')))
    cfgs.write({'acceptance_criteria': criteria, 'text_phrase_mapping': mapping})
    print('  {:<16} {:<12} {:>3} configuraciones'.format(
        spec_name, 'competitivo' if competitivo else 'cualitativo', len(cfgs)))
    return len(cfgs)


print('--- Criterios y mapeo por producto ---')
total  = aplicar('Muestra negativa', False, CUALI_NEG, CUALI_NEG_M)
total += aplicar('Muestra positiva', False, CUALI_POS, CUALI_POS_M)
total += aplicar('Muestra negativa', True,  COMP_NEG,  COMP_NEG_M)
total += aplicar('Muestra positiva', True,  COMP_POS,  COMP_POS_M)
print('  total: {} configuraciones'.format(total))

print('--- Analisis abierto 910 (QC/2026/00481, DMADB01) ---')
detalles = Detail.search([('test_line_id.check_id', '=', 910),
                          ('evaluation_type', '=', 'vama_multi_check')])
sin_p1 = detalles.filtered(lambda d: 'patron #1' not in (d.acceptance_criteria or '')
                           and 'patr\u00f3n #1' not in (d.acceptance_criteria or ''))
con_p1 = detalles - sin_p1
print('  renglones {} (sin patron #1: {}, con patron #1: {})'.format(
    len(detalles), len(sin_p1), len(con_p1)))
sin_p1.write({'acceptance_criteria': COMP_NEG})
con_p1.write({'acceptance_criteria': COMP_POS})

env.cr.commit()
print('Guardado.')
