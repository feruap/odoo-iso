# -*- coding: utf-8 -*-
"""Las 4 soluciones de captura que faltaban, y la hoja correcta de DMTSH02.

Mery, 28-sep-2026, sobre el archivo que devolvio ajustado:

  - La membrana lleva hasta tres lineas: prueba, referencia y control. La de
    CONTROL es la misma en las 15 hojas: anti-raton, que es lo que atrapa al
    conjugado de control (SPALMA03, anticuerpo de raton).
  - Faltaban ademas las de p24, TSH y Salmonella typhi. El anticuerpo de las
    cuatro ya estaba en el catalogo.
  - DMTSH02 (semicuantitativa) consumia SPHMC37, que es la hoja CUALITATIVA.
    Le toca SPHMC52.

Se copian los atributos de SPSCA01, que ya quedo acordada: 3 dias, sin
analisis, ml, se fabrica, lote con prefijo de clave.

Idempotente.
"""
MODELO = 'SPSCA01'

NUEVAS = [
    ('SPSCA25', 'Solución de captura anti-ratón'),
    ('SPSCA26', 'Solución de captura anti-p24 del VIH 1'),
    ('SPSCA27', 'Solución de captura anti-TSH'),
    ('SPSCA28', 'Solución de captura anti-Salmonella typhi'),
]

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
assert mery, 'No se encontro el usuario de Mery'
env = env(user=mery.id, context=dict(env.context, amunet_alta_autorizada=True))

modelo = env['product.product'].search([('default_code', '=', MODELO)], limit=1)
assert modelo, 'No existe el modelo %s' % MODELO
tm = modelo.product_tmpl_id

base = {
    'type': tm.type, 'is_storable': tm.is_storable, 'tracking': 'lot',
    'categ_id': tm.categ_id.id, 'uom_id': tm.uom_id.id,
    'sale_ok': False, 'purchase_ok': False,
    'amunet_destino_almacen': tm.amunet_destino_almacen,
    'amunet_resguardo_aru': tm.amunet_resguardo_aru,
    'amunet_etapa_ll': tm.amunet_etapa_ll,
    'amunet_lot_reset_monthly': True,
    'amunet_expiration_text': tm.amunet_expiration_text,
    'amunet_req_quality_control': False, 'qc_required': False,
    'route_ids': [(6, 0, tm.route_ids.ids)],
}

creados, existentes = [], []
for clave, nombre in NUEVAS:
    ya = env['product.product'].search([('default_code', '=', clave)], limit=1)
    if ya:
        existentes.append(clave)
        continue
    t = env['product.template'].create(dict(base, name=nombre, default_code=clave))
    t.serial_prefix_format = clave[2:]
    t.with_context(lang='es_MX').name = nombre
    creados.append((clave, nombre, t.lot_sequence_id.prefix, t.amunet_expiration_text))

# --- receta de DMTSH02 -----------------------------------------------------
pt02 = env['product.product'].search([('default_code', '=', 'DMTSH02')], limit=1)
h37 = env['product.product'].search([('default_code', '=', 'SPHMC37')], limit=1)
h52 = env['product.product'].search([('default_code', '=', 'SPHMC52')], limit=1)
assert pt02 and h37 and h52, 'Falta DMTSH02 / SPHMC37 / SPHMC52'

lineas = env['mrp.bom.line'].search([
    ('bom_id.product_tmpl_id', '=', pt02.product_tmpl_id.id),
    ('product_id', '=', h37.id)])
cambiadas = []
for l in lineas:
    l.write({'product_id': h52.id})
    cambiadas.append((l.bom_id.display_name, l.product_qty))

env.cr.commit()

print('=' * 74)
for clave, nombre, pref, cad in creados:
    print('CREADA  %-9s %-44s lote %-12s cad %s' % (clave, nombre[:44], pref, cad))
for clave in existentes:
    print('YA ESTABA %s' % clave)
print('-' * 74)
if cambiadas:
    for bom, qty in cambiadas:
        print('DMTSH02: %s  SPHMC37 -> SPHMC52 (%s)' % (bom, qty))
else:
    print('DMTSH02: no habia linea con SPHMC37 (ya estaba corregida?)')
print('-' * 74)
for c in env['mrp.bom.line'].search([('bom_id.product_tmpl_id', '=', pt02.product_tmpl_id.id)]):
    print('  receta DMTSH02: %s x %s' % (c.product_id.default_code, c.product_qty))
print('=' * 74)
