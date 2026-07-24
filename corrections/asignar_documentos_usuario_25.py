# -*- coding: utf-8 -*-
# Asignar el grupo "Documentos: Usuario" (amunet_documentos.group_documentos_user)
# a 25 usuarios, para que puedan leer PNOs y dar acuse de lectura.
# Solicitado por el area de Documentacion. Autorizado por Fernando 2026-07-10.
# Idempotente (no re-agrega). Acceso de solo lectura + acuse.

LOGINS = [
 'a.desarrollo@amunet.com.mx','almacen1@amunet.com.mx','almacen2@amunet.com.mx',
 'almacen.mp@amunet.com.mx','almacen.pt@amunet.com.mx','analista1cc@amunet.com.mx',
 'analista2cc@amunet.com.mx','ensayo@amunet.com.mx','mantenimiento@amunet.com.mx',
 'operador1@amunet.com.mx','operador2@amunet.com.mx','operador3@amunet.com.mx',
 'pcrrapida1@amunet.com.mx','pcrrapida2@amunet.com.mx','pcrrapida3@amunet.com.mx',
 'practicante.cc@amunet.com.mx','practicante.de@amunet.com.mx','practicante.sol@amunet.com.mx',
 'produccionsub@amunet.com.mx','rrhh@amunet.com.mx','s.controldecalidad@amunet.com.mx',
 'soluciones@amunet.com.mx','s.produccion@amunet.com.mx','supalmacen@amunet.com.mx',
 's.validacion@amunet.com.mx',
]

g = env.ref('amunet_documentos.group_documentos_user')
existing = set(g.user_ids.ids)
added = 0
skip = 0
missing = []
for l in LOGINS:
    u = env['res.users'].search([('login', '=', l)], limit=1)
    if not u:
        missing.append(l)
        continue
    if u.id in existing:
        skip += 1
        continue
    g.sudo().write({'user_ids': [(4, u.id)]})
    added += 1
    print("  + %s" % l)

env.cr.commit()
print("AGREGADOS:", added, "| YA TENIAN:", skip, "| NO EXISTEN:", missing)
print("TOTAL en 'Documentos: Usuario':", len(g.user_ids))
