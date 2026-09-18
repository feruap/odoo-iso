# Clasifica los productos por etapa de linea larga.
Tmpl = env['product.template']

conj = Tmpl.search([('amunet_es_conjugado', '=', True)])
conj.write({'amunet_etapa_ll': 'conjugados'})
print('conjugados : %s productos' % len(conj))

sol = Tmpl.search([
    ('categ_id.complete_name', 'ilike', 'soluc'),
    ('amunet_es_conjugado', '=', False),
])
sol.write({'amunet_etapa_ll': 'soluciones'})
print('soluciones : %s productos' % len(sol))

for etapa in ('inyeccion', 'laminado'):
    n = Tmpl.search_count([('amunet_etapa_ll', '=', etapa)])
    print('%-11s: %s productos' % (etapa, n))

env.cr.commit()
print('COMMIT OK')
