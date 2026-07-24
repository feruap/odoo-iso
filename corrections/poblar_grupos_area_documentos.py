# Puebla los grupos de area de amunet_documentos replicando las asignaciones de
# staging (confirmadas por Fernando 2026-07-22). Se corre JUSTO despues del -u
# que crea los grupos + las ir.rule, para que ningun usuario pierda acceso a los
# documentos de su area. Idempotente (usa (4,) link).
ASIGN = {
    'amunet_documentos.group_docs_area_al': [
        'almacen1@amunet.com.mx', 'almacen2@amunet.com.mx', 'almacen.mp@amunet.com.mx',
        'almacen.pt@amunet.com.mx', 'supalmacen@amunet.com.mx'],
    'amunet_documentos.group_docs_area_cc': [
        'analista1cc@amunet.com.mx', 'analista2cc@amunet.com.mx', 'ensayo@amunet.com.mx',
        'practicante.cc@amunet.com.mx', 's.controldecalidad@amunet.com.mx'],
    'amunet_documentos.group_docs_area_pr': [
        'operador1@amunet.com.mx', 'operador2@amunet.com.mx', 'operador3@amunet.com.mx',
        'pcrrapida1@amunet.com.mx', 'pcrrapida2@amunet.com.mx', 'pcrrapida3@amunet.com.mx',
        'produccionsub@amunet.com.mx', 's.produccion@amunet.com.mx'],
    'amunet_documentos.group_docs_area_rh': ['rrhh@amunet.com.mx'],
}
for gxml, logins in ASIGN.items():
    g = env.ref(gxml, raise_if_not_found=False)
    if not g:
        print('OJO grupo no existe:', gxml)
        continue
    users = env['res.users'].sudo().search([('login', 'in', logins)])
    faltan = set(logins) - set(users.mapped('login'))
    g.sudo().write({'user_ids': [(4, u.id) for u in users]})
    print(gxml.split('.')[-1], '-> asignados', len(users), 'usuarios', ('| faltan: %s' % faltan) if faltan else '')
env.cr.commit()
print('LISTO')
