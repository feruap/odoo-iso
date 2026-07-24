# -*- coding: utf-8 -*-
# Limpieza de datos DEMO de capacitacion (autorizado por Fernando 2026-07-11):
#  - CAP-0003: registro del usuario FALSO "Calidad 2" (Calidad2@correo.ejemplo.com, inactivo).
#  - CAP-0002: registro del admin deshabilitado, mismo parametro demo CV-01.
#  - Parametro CV-01 (id 125) "*Coeficiente de variacion": huerfano, NO usado en
#    ningun control real (0 lineas de analisis / spec_configs / productos).
#  - Usuario falso "Calidad 2" (uid 57): se intenta borrar; si FK lo impide, se
#    deja inactivo y etiquetado.
# NO toca la cuenta admin (uid 2), solo su registro de capacitacion demo.

Reg = env['amunet.registro.capacitacion']
Param = env['amunet.quality.check.parameter']
Users = env['res.users']

# 1) Borrar los 2 registros demo
regs = Reg.search([('name', 'in', ['CAP-0002', 'CAP-0003'])])
print("registros demo a borrar:", regs.mapped('name'))
regs.unlink()
print("registros borrados.")

# 2) Borrar el parametro CV-01 (125) si quedo huerfano
p = Param.browse(125).exists()
if p and p.code == 'CV-01':
    n_reg = Reg.search_count([('parameter_id', '=', 125)])
    if n_reg == 0:
        p.unlink()
        print("CV-01 (125) borrado.")
    else:
        print("CV-01 aun referenciado por", n_reg, "registros, NO se borra.")
else:
    print("CV-01 (125) no encontrado o codigo distinto, se omite.")

# 3) Usuario falso Calidad 2 (uid 57)
u = Users.browse(57).exists()
if u and not u.active and u.login == 'Calidad2@correo.ejemplo.com':
    partner = u.partner_id
    try:
        u.unlink()
        print("usuario falso 57 BORRADO.")
        # limpiar partner si ya no cuelga de un usuario y no rompe nada
        try:
            partner.unlink()
            print("partner del usuario falso borrado.")
        except Exception as e:
            print("partner conservado (referencias):", str(e)[:60])
    except Exception as e:
        print("no se pudo borrar el usuario (FK); se deja INACTIVO:", str(e)[:80])
else:
    print("usuario 57 no coincide con el falso esperado, se omite por seguridad.")

env.cr.commit()
print("LIMPIEZA LISTA.")
