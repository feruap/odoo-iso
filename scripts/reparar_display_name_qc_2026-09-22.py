# Recalcula los campos almacenados de los bloques de parametros de calidad que
# quedaron vacios por haberse insertado fuera de la ORM (create_date NULL).
# Sin ellos la vista pinta 'false' en lugar del nombre del parametro.
Rel = env['amunet.quality.parameter.product.rel']
CAMPOS = ['parameter_code', 'parameter_name', 'display_name',
          'spec_summary', 'active_spec_count']

recs = Rel.with_context(active_test=False).search([])
malos = recs.filtered(lambda r: not r.display_name)
print('bloques totales: %s | sin nombre: %s (activos: %s)'
      % (len(recs), len(malos), len(malos.filtered('active'))))

for campo in CAMPOS:
    env.add_to_compute(Rel._fields[campo], malos)
malos.flush_recordset()
env.cr.commit()

quedan = Rel.with_context(active_test=False).search([]).filtered(lambda r: not r.display_name)
print('despues del recalculo, sin nombre: %s' % len(quedan))
for r in malos[:12]:
    print('   %-6s %-10s %s' % (r.id, r.product_tmpl_id.default_code or '-', r.display_name))
