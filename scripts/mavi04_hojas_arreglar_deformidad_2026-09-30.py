"""Corrige dos efectos de mi propio script anterior en las 10 hojas de MAVI-04.

Lo aplique en produccion el 30-sep-2026 y dejo dos cosas mal, porque no contemplo ni el
nombre variante ni el duplicado del mismo nombre:

 1. NUEVE hojas quedaron con "Deformidad o deterioro" DOS VECES. El renglon bueno esta en
    seq 30 con su criterio; el sobrante esta en seq 99 o 40, con criterio vacio o con
    "Sin deformidad" a secas. Mi script solo apagaba lo que NO era de los 3 estandar, y
    un duplicado del nombre estandar no entraba en esa regla.

 2. SPHMC34 quedo con SOLO DOS renglones. El suyo se llama "Deformidad" -- sin "o
    deterioro"-, asi que mi normalizador lo tomo por nombre ajeno y lo apago. Su criterio
    dice "Sin deformidad o deteriodo", con una errata, lo que confirma que es el renglon
    de deformidad de esa hoja y no otro.

QUE HACE:
    - en las hojas con duplicado: conserva el que tiene criterio real -- entre uno vacio y
      uno a medias, el de texto completo- y apaga el otro. El que se queda recibe la
      secuencia 30 y el texto estandar.
    - en SPHMC34: reactiva su renglon de "Deformidad" y le pone el texto estandar y la
      secuencia 30. No se crea nada nuevo: se recupera el que ya existia.

El texto estandar es el de los 104 productos terminados, aprobado por Diana y confirmado
contra la base: "Sin deformidad o deterioro" / "Con deformidad o deterioro", en minuscula
y sin punto final.

Al terminar, cada una de las 10 hojas debe tener EXACTAMENTE 3 renglones. El script lo
comprueba y lo dice.

Idempotente.
"""
Rel = env['amunet.quality.parameter.product.rel'].sudo()
Cfg = env['amunet.quality.parameter.specification.config'].sudo()
RelX = Rel.with_context(active_test=False); CfgX = Cfg.with_context(active_test=False)

HOJAS = ['SPHMC34', 'SPHMC77', 'SPHMC78', 'SPHMC79',
         'SPHMT07', 'SPHMT08', 'SPHMT09', 'SPHMT10', 'SPHMT11', 'SPHMT12']
PASA, FALLA = 'Sin deformidad o deterioro', 'Con deformidad o deterioro'

def es_deformidad(c):
    n = (c.specification_name or c.specification_id.name or '').strip().lower()
    return n.startswith('deformidad')

print('=== arreglando el renglon de Deformidad ===')
for clave in HOJAS:
    t = env['product.template'].sudo().search([('default_code', '=', clave)], limit=1)
    if not t:
        print('   [ojo] no existe %s' % clave); continue
    for rel in RelX.search([('product_tmpl_id', '=', t.id),
                            ('parameter_id.code', '=', 'MAVI-04'), ('active', '=', True)]):
        activos = CfgX.search([('product_parameter_rel_id', '=', rel.id), ('active', '=', True)])
        defs = activos.filtered(es_deformidad)

        if len(defs) > 1:
            # se conserva el de criterio mas completo
            def puntua(c):
                crit = (c.acceptance_criteria or '').strip().lower()
                if not crit: return 0
                if crit == PASA.lower(): return 3
                return 2
            mejor = max(defs, key=lambda c: (puntua(c), -c.id))
            for c in defs - mejor:
                c.write({'active': False})
                print('   %-9s apagado el duplicado cfg %-6s seq %-4s crit="%s"' % (
                    clave, c.id, c.sequence, (c.acceptance_criteria or '(vacio)')[:28]))
            defs = mejor
        elif not defs:
            # SPHMC34: su renglon de deformidad quedo archivado por mi script
            cand = CfgX.search([('product_parameter_rel_id', '=', rel.id), ('active', '=', False)]).filtered(es_deformidad)
            if not cand:
                print('   [ALTO] %s no tiene ningun renglon de deformidad, ni activo ni archivado' % clave)
                continue
            defs = cand.sorted(lambda c: -len(c.acceptance_criteria or ''))[0]
            defs.write({'active': True})
            print('   %-9s reactivado cfg %-6s "%s"  crit original="%s"' % (
                clave, defs.id, defs.specification_name or defs.specification_id.name,
                (defs.acceptance_criteria or '(vacio)')[:30]))

        # el que queda: texto estandar y su lugar en la lista
        c = defs[0] if hasattr(defs, '__len__') and len(defs) else defs
        vals = {}
        if (c.binary_option_pass or '') != PASA: vals['binary_option_pass'] = PASA
        if (c.binary_option_fail or '') != FALLA: vals['binary_option_fail'] = FALLA
        if (c.acceptance_criteria or '') != PASA: vals['acceptance_criteria'] = PASA
        if c.binary_expected_option != 'with_prefix': vals['binary_expected_option'] = 'with_prefix'
        if c.sequence != 30: vals['sequence'] = 30
        if vals:
            c.write(vals)
            print('   %-9s ajustado cfg %-6s -> seq 30, criterio "%s"' % (clave, c.id, PASA))

print('\n=== comprobacion: cada hoja debe tener EXACTAMENTE 3 ===')
todo_bien = True
for clave in HOJAS:
    t = env['product.template'].sudo().search([('default_code', '=', clave)], limit=1)
    for rel in RelX.search([('product_tmpl_id', '=', t.id),
                            ('parameter_id.code', '=', 'MAVI-04'), ('active', '=', True)]):
        act = Cfg.search([('product_parameter_rel_id', '=', rel.id), ('active', '=', True)],
                         order='sequence, id')
        marca = 'ok' if len(act) == 3 else '*** %d, REVISAR ***' % len(act)
        if len(act) != 3:
            todo_bien = False
        print('   %-9s %d renglones  %s' % (clave, len(act), marca))
        for c in act:
            print('        %-4s %-24s "%s"' % (
                c.sequence, (c.specification_name or c.specification_id.name or '?')[:24],
                (c.acceptance_criteria or '(vacio)')[:30]))
print('\n   %s' % ('todas las hojas con sus 3 renglones' if todo_bien else 'QUEDAN HOJAS POR REVISAR'))
env.cr.commit()
