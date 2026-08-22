# Renombra el producto DIAM-023 al nombre corto que pidio Fernando.
# name es traducible -> se escribe en en_US y es_MX (si no, el usuario sigue
# viendo el viejo). Autorizado por Fernando 2026-07-23.
NUEVO = 'COVID19 IgG/IgM'
t = env['product.template'].sudo().search([('default_code', '=', 'DIAM-023')], limit=1)
assert t, 'DIAM-023 no existe'
print('Antes:', t.name)
t.with_context(lang='en_US').write({'name': NUEVO})
t.with_context(lang='es_MX').write({'name': NUEVO})
env.cr.commit()
tt = env['product.template'].sudo().browse(t.id)
print('en_US:', tt.with_context(lang='en_US').name)
print('es_MX:', tt.with_context(lang='es_MX').name)
print('LISTO')
