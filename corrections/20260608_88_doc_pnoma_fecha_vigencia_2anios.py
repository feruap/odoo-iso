# Corrección: PNOMA-001 a 004 tenían fecha_vigencia = 2027-07-01 (3 años)
# El estándar es 2 años de vigencia. Se corrige a 2026-07-01.
# El error venía desde los documentos Word originales.
#
# SQL equivalente:
# UPDATE amunet_documento SET fecha_vigencia = '2026-07-01'
# WHERE codigo LIKE 'PNOMA%' AND fecha_vigencia = '2027-07-01';

DocModel = env['amunet.documento']
docs = DocModel.search([('codigo', 'like', 'PNOMA-%'), ('fecha_vigencia', '=', '2027-07-01')])
for doc in docs:
    doc.write({'fecha_vigencia': '2026-07-01'})
env.cr.commit()
print(f'Corregidos {len(docs)} registros PNOMA')
