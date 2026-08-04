# -*- coding: utf-8 -*-
# Crea el producto generico no-codificado-por-equipo para el ingreso de
# equipos de uso interno (B-almacenable, tracking por serie).
CODE = 'EQUIPO-USO-INTERNO'
existing = env['product.template'].with_context(active_test=False).search(
    [('default_code', '=', CODE)], limit=1)
if existing:
    print("Ya existe:", existing.default_code, existing.id)
else:
    tmpl = env['product.template'].with_context(amunet_alta_autorizada=True).create({
        'name': 'Equipo de uso interno',
        'default_code': CODE,
        'type': 'consu',
        'is_storable': True,      # almacenable (mantiene la serie en ubicacion)
        'tracking': 'serial',     # numero de serie por unidad
        'purchase_ok': True,
        'sale_ok': False,
    })
    print("Creado:", tmpl.default_code, "id", tmpl.id,
          "| type:", tmpl.type, "| is_storable:", tmpl.is_storable,
          "| tracking:", tmpl.tracking)
env.cr.commit()
