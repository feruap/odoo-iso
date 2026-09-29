"""Limpia las especificaciones de calidad duplicadas.

Autorizado por Mery el 29-sep-2026.

QUE ES UN DUPLICADO AQUI: dos o mas especificaciones ACTIVAS del mismo producto y
el mismo parametro, con el MISMO nombre, el mismo rango y el mismo criterio de
aceptacion. Son el mismo renglon repetido: al capturar un analisis aparecen dos
veces y hay que llenar las dos.

NO cuentan como duplicado, y por eso no se tocan:
  - las inactivas (hay muchas de febrero con el nombre del parametro como
    marcador; ya estan apagadas y no salen en ningun analisis);
  - las que comparten nombre pero tienen valores distintos -- por ejemplo
    "Variacion de volumen" para presentaciones de 1000 ul y de 2.5 ml: se llaman
    igual y son especificaciones diferentes.

Un primer conteo sin esos dos filtros daba 1,746 casos; los reales son 26 grupos
con 35 registros sobrantes.

QUE HACE: de cada grupo conserva el de id MENOR -- el original -- y de los
sobrantes:
  - si NINGUN analisis lo referencia, lo borra;
  - si algun analisis lo referencia, NO lo borra: lo desactiva, para que deje de
    aparecer en los analisis nuevos sin romper el expediente de los que ya lo
    usaron. Y si ese analisis esta cerrado o firmado, no se toca en absoluto:
    lo firmado es historia.

Idempotente.
"""

Cfg = env['amunet.quality.parameter.specification.config'].sudo()
Detail = env['amunet.quality.test.line.detail'].sudo()
Check = env['amunet.quality.check'].sudo()

todas = Cfg.search([('active', '=', True)])
grupos = {}
for c in todas:
    rel = c.product_parameter_rel_id
    if not rel or not rel.active:
        continue
    clave = (rel.product_tmpl_id.id, rel.parameter_code or '',
             (c.specification_name or '').strip(), c.min_value, c.max_value,
             (c.acceptance_criteria or '').strip())
    grupos.setdefault(clave, []).append(c)

duplicados = {k: v for k, v in grupos.items() if len(v) > 1}
print('grupos con duplicados: %s   registros sobrantes: %s' % (
    len(duplicados), sum(len(v) - 1 for v in duplicados.values())))

borrados, desactivados, intocados = [], [], []
for clave, lista in sorted(duplicados.items(), key=lambda x: (x[0][0], x[0][1])):
    lista.sort(key=lambda c: c.id)
    conserva, sobrantes = lista[0], lista[1:]
    prod = conserva.product_parameter_rel_id.product_tmpl_id.default_code
    param = conserva.product_parameter_rel_id.parameter_code
    print('\n%s / %s / %s  -> conserva %s, sobran %s' % (
        prod, param, clave[2][:40], conserva.id, [c.id for c in sobrantes]))
    for c in sobrantes:
        usos = Detail.search([('specification_config_id', '=', c.id)])
        cerrados = usos.filtered(
            lambda d: d.check_id.state == 'done' or d.check_id.user_authorized_id)
        if cerrados:
            intocados.append((prod, param, c.id, 'usada en analisis cerrado: %s'
                              % ', '.join(sorted(set(cerrados.mapped('check_id.name'))))))
            print('   %s NO se toca: %s' % (c.id, intocados[-1][3]))
            continue
        if usos:
            c.write({'active': False})
            desactivados.append((prod, param, c.id, len(usos)))
            print('   %s desactivada (la usan %s analisis abiertos, no se borra)' % (
                c.id, len(usos)))
            continue
        cid = c.id
        try:
            c.unlink()
            borrados.append((prod, param, cid))
            print('   %s borrada (nadie la usaba)' % cid)
        except Exception as e:
            c.write({'active': False})
            desactivados.append((prod, param, cid, 0))
            print('   %s no se pudo borrar, se desactiva: %s' % (cid, str(e)[:80]))

print('\n=== resumen ===')
print('   borradas:      %s' % len(borrados))
print('   desactivadas:  %s' % len(desactivados))
print('   sin tocar:     %s' % len(intocados))
for p, pa, i, m in intocados:
    print('      %-10s %-10s %s  %s' % (p, pa, i, m))

restantes = 0
todas2 = Cfg.search([('active', '=', True)])
g2 = {}
for c in todas2:
    rel = c.product_parameter_rel_id
    if not rel or not rel.active:
        continue
    k = (rel.product_tmpl_id.id, rel.parameter_code or '',
         (c.specification_name or '').strip(), c.min_value, c.max_value,
         (c.acceptance_criteria or '').strip())
    g2.setdefault(k, []).append(c)
restantes = sum(len(v) - 1 for v in g2.values() if len(v) > 1)
print('\n   sobrantes que quedan: %s' % restantes)
env.cr.commit()
