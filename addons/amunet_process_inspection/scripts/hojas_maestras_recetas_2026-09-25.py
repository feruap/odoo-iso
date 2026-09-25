"""Recetas de las 15 hojas maestras que se laminan en Amunet.

APLICADO EN STAGING el 25-sep-2026. **NO en produccion todavia**: falta que Mery
llene el conjugado de cada hoja y los ml (archivo 'Conjugado por hoja maestra
2026-09-25.xlsx', subido a su chat de Discuss).

Fuente: 'Hojas maestras - cual se lamina aqui.xlsx' que subio Mery, hoja
'Amunet'. Ella marco 15 de las 96 como "se lamina aqui".

Cantidades que indico Mery:
  - UNA almohadilla por hoja fabricada (la receta produce 30 cm = una hoja)
  - membrana: 31 cm por hoja. Viene en ROLLOS DE 100 METROS, asi que son
    31/10000 = **0.0031 rollos**. Esta linea NO se carga aqui: se agrega junto
    con los conjugados para no mandar dos versiones a produccion.

Lo que falta y por que no se puede inventar:
  - el CONJUGADO de cada hoja (control y prueba). El anticuerpo no va directo:
    entra por las soluciones y los conjugados. Hay 29 SPCDE dados de alta.
  - los ml de conjugado por hoja.
  - SPALMA14 en la receta de SPHMC15 (Influenza A+B): ya se dio de alta el
    25-sep (PR #115), falta agregarla a esa receta.

Dos que no se pudieron asignar solas:
  - SPHMC07 Hemoglobina: el unico parecido es SPCDE13, que dice "hemoglobina
    glicada" (HbA1c), otra prueba.
  - SPHMT01 Biotina: es hoja molecular; el candidato seria SPCDE03
    anti-fluoresceina, pero es suposicion.

Idempotente: busca por clave y no duplica lineas.
"""
FORMULAS = {
 'SPHMC01': ['MPTS01','SPALMA03','SPALMA01','SPALMA04'],
 'SPHMC18': ['MPTS01','SPALMA03','SPALMA01','SPALMA13','SPALMA09','SPALMA07'],
 'SPHMC19': ['MPTS01','SPALMA03','SPALMA01','SPALMA13','SPALMA09','SPALMA07'],
 'SPHMC15': ['MPTS01','SPALMA03','SPALMA02','SPALMA14','SPALMA05'],
 'SPHMC24': ['MPTS01','SPALMA03','SPALMA01','SPALMA13','SPALMA07'],
 'SPHMC38': ['MPTS01','SPALMA03','SPALMA01','SPALMA13','SPALMA07'],
 'SPHMC20': ['MPTS01','SPALMA03','SPALMA01','SPALMA05'],
 'SPHMC22': ['MPTS01','SPALMA03','SPALMA01','SPALMA13','SPALMA07'],
 'SPHMC23': ['MPTS01','SPALMA03','SPALMA01','SPALMA13','SPALMA07'],
 'SPHMC09': ['MPTS02','SPALMA03','SPALMA01','SPALMA13','SPALMA07'],
 'SPHMT01': ['MPTS01','SPALMA03','SPALMA01','SPALMA05'],
 'SPHMC07': ['MPTS01','SPALMA03','SPALMA01','SPALMA13','SPALMA05'],
 'SPHMC45': ['MPTS01','SPALMA03','SPALMA01','SPALMA05'],
 'SPHMC37': ['MPTS01','SPALMA03','SPALMA01','SPALMA13','SPALMA07'],
 'SPHMC52': ['MPTS01','SPALMA03','SPALMA01','SPALMA13','SPALMA07'],
}
# la membrana de cada una, para cuando se cargue con su 0.0031 de rollo
MEMBRANA = {'SPHMC01':'MPMNC02','SPHMC18':'MPMNC03','SPHMC19':'MPMNC03','SPHMC15':'MPMNC03',
 'SPHMC24':'MPMNC03','SPHMC38':'MPMNC03','SPHMC20':'MPMNC02','SPHMC22':'MPMNC03',
 'SPHMC23':'MPMNC03','SPHMC09':'MPMNC03','SPHMT01':'MPMNC02','SPHMC07':'MPMNC03',
 'SPHMC45':'MPMNC02','SPHMC37':'MPMNC03','SPHMC52':'MPMNC03'}

Line = env['mrp.bom.line']
unidad = env.ref('uom.product_uom_unit')
faltantes = []

for code, comps in FORMULAS.items():
    t = env['product.template'].search([('default_code','=',code)], limit=1)
    if not t:
        faltantes.append(code); continue
    bom = env['mrp.bom'].search([('product_tmpl_id','=',t.id)], limit=1)
    if not bom:
        faltantes.append('receta de %s' % code); continue
    # la tarjeta correcta: si la formula pide MPTS02, quitar la MPTS01 que traia
    if 'MPTS02' in comps:
        bom.bom_line_ids.filtered(lambda l: l.product_id.default_code == 'MPTS01').unlink()
    # fuera la almohadilla generica que estaba de relleno
    bom.bom_line_ids.filtered(
        lambda l: l.product_id.default_code == 'SPALMA12'
        and 'SPALMA12' not in comps).unlink()
    agregados = []
    for c in comps:
        p = env['product.product'].search([('default_code','=',c)], limit=1)
        if not p:
            faltantes.append('%s (componente de %s)' % (c, code)); continue
        if p.id in bom.bom_line_ids.mapped('product_id').ids:
            continue
        Line.create({'bom_id': bom.id, 'product_id': p.id,
                     'product_qty': 1.0, 'product_uom_id': unidad.id})
        agregados.append(c)
    print('%-9s produce %g %s -> %s' % (code, bom.product_qty, bom.product_uom_id.name,
          ', '.join('%s x%g' % (l.product_id.default_code, l.product_qty) for l in bom.bom_line_ids)))
    if agregados:
        t.message_post(body=(
            'Receta completada el 25-sep-2026 con la formulacion del archivo '
            '<b>Hojas maestras - cual se lamina aqui</b>.<br/>Agregados: %s'
            '<br/><br/><b>Falta la membrana %s</b> (0.0031 rollos por hoja: 31 cm '
            'de un rollo de 100 m) y <b>el conjugado</b>: el anticuerpo no va '
            'directo, entra por las soluciones y los conjugados.'
        ) % (', '.join(agregados), MEMBRANA.get(code, '?')))

if faltantes:
    print('\nFALTANTES: %s' % ', '.join(faltantes))
else:
    env.cr.commit()
    print('\nOK: guardado.')
