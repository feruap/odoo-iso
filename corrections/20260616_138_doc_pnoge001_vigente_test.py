Doc = env['amunet.documento']
doc = Doc.search([('codigo', '=', 'PNOGE-001')], limit=1, order='id desc')
print('Documento: %s v%s estado=%s id=%d' % (doc.codigo, doc.version_actual, doc.state, doc.id))

doc._workflow_write({
    'state': 'vigente',
    'firma_revisa_id': 2,
    'fecha_revisa': '2026-06-16',
    'firma_aprueba_id': 67,
    'fecha_aprueba': '2026-06-16',
    'fecha_publicacion': '2026-06-16',
    'fecha_emision': '2026-06-16',
})
env.cr.commit()
print('Listo: %s ahora esta en estado=%s' % (doc.codigo, doc.state))
