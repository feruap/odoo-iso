# Clasifica los productos por etapa de linea larga.
#
# IMPORTANTE: este script debe poder correrse ANTES de que exista el campo
# amunet_es_conjugado, que lo crea amunet_production. El 18-sep-2026 se corrio
# justo despues de desplegar el filtro por etapa -- cuando ese campo todavia no
# existia en produccion -- y reventó en la cuarta linea:
#
#   ValueError: Invalid field product.template.amunet_es_conjugado
#
# Fallo en el momento mas delicado: el filtro por etapa ya estaba arriba y sin
# esta clasificacion una orden de Soluciones se queda SIN PRODUCTOS que elegir.
# Por eso ahora se comprueba que el campo exista antes de usarlo, y el script
# funciona en cualquier orden de despliegue.
Tmpl = env['product.template']
hay_conjugados = 'amunet_es_conjugado' in Tmpl._fields

if hay_conjugados:
    conj = Tmpl.search([('amunet_es_conjugado', '=', True)])
    conj.write({'amunet_etapa_ll': 'conjugados'})
    print('conjugados : %s productos' % len(conj))
else:
    print('conjugados : el campo amunet_es_conjugado todavia no existe; '
          'se omite. Vuelve a correr el script despues de desplegar '
          'amunet_production para clasificarlos.')

dom_sol = [('categ_id.complete_name', 'ilike', 'soluc')]
if hay_conjugados:
    dom_sol.append(('amunet_es_conjugado', '=', False))
sol = Tmpl.search(dom_sol)
sol.write({'amunet_etapa_ll': 'soluciones'})
print('soluciones : %s productos' % len(sol))

for etapa in ('inyeccion', 'laminado'):
    n = Tmpl.search_count([('amunet_etapa_ll', '=', etapa)])
    print('%-11s: %s productos' % (etapa, n))

env.cr.commit()
print('COMMIT OK')
