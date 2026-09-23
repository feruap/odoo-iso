# -*- coding: utf-8 -*-
"""Alta de DLTB02 (TB-DxNET): identidad, BoM de linea corta y presentacion.

Se calca la estructura de DLVPH01, que es el patron ya validado de los
moleculares de lote 12 (VPH, ECOHEM e ISOLISTER son identicos entre si).

Decisiones de Mery, 18-sep-2026:
  - El catalogo de pruebas rapidas manda: el nombre es TB-DxNET.
  - Vial STBBM01 (el estandar), no el de 250 uL.
  - Subtipo de etiqueta M (molecular), como VPH.
  - Caja de 12 y lote de 12: un lote llena una caja y el lote queda limpio.
  - Receta de LINEA CORTA mientras se pule la larga para PCR.

PENDIENTE a proposito: el primer mix / diana NO se da de alta aqui. Ningun
BoM molecular registra la diana hoy, y por eso paso inadvertida la
contradiccion del manual V3.3 (declara 16S) contra el expediente de diseno
(declara IS1081). Cuando el laboratorio confirme cual lleva el kit que se
vende, se agrega como una linea mas del BoM.

Idempotente: se puede volver a correr sin duplicar nada.
"""
CLAVE = 'DLTB02'
MODELO = 'DLVPH01'

PT = env['product.template']
prod = PT.search([('default_code', '=', CLAVE)], limit=1)
assert prod, 'No existe %s' % CLAVE
modelo = PT.search([('default_code', '=', MODELO)], limit=1)
assert modelo, 'No existe el producto modelo %s' % MODELO

# ── 1. IDENTIDAD (del catalogo de pruebas rapidas, que es la fuente) ────────
cat = env['amunet.prueba.rapida'].search([('referencia', '=', CLAVE)], limit=1)
assert cat, 'No hay registro en el catalogo de pruebas rapidas para %s' % CLAVE
vals = {
    'nombre_etiqueta': cat.nombre_texto,              # TB-DxNET
    'amunet_expiration_text': cat.caducidad_autorizada,  # 6 meses
    'registro_sanitario': cat.registro_sanitario,     # 1255R2026 SSA
    'etiqueta_subtipo': 'M',
}
antes = {k: prod[k] for k in vals}
prod.sudo().write(vals)
print('IDENTIDAD:')
for k, v in vals.items():
    print('   %-26s %r -> %r' % (k, antes[k], v))

# ── 2. BoM de linea corta, calcado de VPH ───────────────────────────────────
bom_modelo = env['mrp.bom'].search(
    [('product_tmpl_id', '=', modelo.id), ('active', '=', True)], limit=1)
assert bom_modelo, 'El modelo %s no tiene BoM activo' % MODELO

bom = env['mrp.bom'].search([('product_tmpl_id', '=', prod.id)], limit=1)
if not bom:
    bom = env['mrp.bom'].sudo().create({'product_tmpl_id': prod.id})
bom.sudo().write({
    'code': 'RUTA-CORTA-PCR-12-%s' % CLAVE,
    'product_qty': bom_modelo.product_qty,      # 12
    'product_uom_id': bom_modelo.product_uom_id.id,
    'type': 'normal',
    'active': True,
})

# componentes: los mismos del modelo, mismas cantidades
bom.bom_line_ids.sudo().unlink()
print('COMPONENTES (copiados de %s):' % MODELO)
for l in bom_modelo.bom_line_ids:
    env['mrp.bom.line'].sudo().create({
        'bom_id': bom.id,
        'product_id': l.product_id.id,
        'product_qty': l.product_qty,
        'product_uom_id': l.product_uom_id.id,
        'sequence': l.sequence,
    })
    print('   %-10s %8.2f  (%.2f/pza)' % (
        l.product_id.default_code, l.product_qty, l.product_qty / bom.product_qty))

# ── 3. Ruta: los 8 pasos del modelo, renombrados a TB-DxNET ─────────────────
bom.operation_ids.sudo().unlink()
print('RUTA (8 pasos de %s):' % MODELO)
for op in bom_modelo.operation_ids.sorted('sequence'):
    nombre = (op.name or '').replace('VPH-NET', cat.nombre_texto)
    env['mrp.routing.workcenter'].sudo().create({
        'bom_id': bom.id,
        'name': nombre,
        'workcenter_id': op.workcenter_id.id,
        'sequence': op.sequence,
        'time_cycle_manual': op.time_cycle_manual,
    })
    print('   %3d  %-52s %s' % (op.sequence, nombre, op.workcenter_id.name))

# ── 4. Presentacion autorizada: caja de 12, como los demas moleculares ──────
Pres = env['amunet.packaging.presentation']
pres_modelo = Pres.search([('product_tmpl_id', '=', modelo.id)], limit=1)
pres = Pres.search([('product_tmpl_id', '=', prod.id),
                    ('package_qty', '=', 12)], limit=1)
pvals = {
    'product_tmpl_id': prod.id,
    'name': 'Caja con 12 pruebas',
    'package_qty': 12,
    'is_authorized': True,
    'label_required': pres_modelo.label_required if pres_modelo else True,
    'manual_required': pres_modelo.manual_required if pres_modelo else False,
}
if pres:
    pres.sudo().write(pvals)
else:
    pres = Pres.sudo().create(pvals)
print('PRESENTACION: %s (%d pzs) autorizada=%s' % (
    pres.name, pres.package_qty, pres.is_authorized))

env.cr.commit()
print('COMMIT OK')
