# -*- coding: utf-8 -*-
# Ajustes de Fernando a las recetas de soluciones (revisados del archivo
# Recetas_Soluciones subido a Discuss). Autorizado 2026-07-11.
#  - SPACL01 (Acido cloroaurico 1%): caducidad = "1 día"
#  - SPCDS01 (Citrato de sodio 1%):  caducidad = "1 día"
#  - SPHBB01 (Corrimiento Hemoglobina Cualitativa): pH = 9 (antes 8)
Tmpl = env['product.template']
CAMBIOS = [
    ('SPACL01', {'amunet_expiration_text': '1 día'}),
    ('SPCDS01', {'amunet_expiration_text': '1 día'}),
    ('SPHBB01', {'amunet_initial_ph': 9}),
]
for code, vals in CAMBIOS:
    t = Tmpl.search([('default_code', '=', code)], limit=1)
    if t:
        t.write(vals)
        print("  %s -> %s" % (code, vals))
    else:
        print("  %s NO EXISTE" % code)
env.cr.commit()
print("LISTO")
