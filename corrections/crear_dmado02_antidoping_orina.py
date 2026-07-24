# -*- coding: utf-8 -*-
# Completa el producto DMADO02 "ANTIDOPING ORINA 5P" (linea corta) en produccion.
# El producto YA existe como cascaron (sin secuencia, sin BoM, sin presentacion).
# Autorizado por Fernando 2026-07-13. Idempotente: no duplica lo que ya exista.
#
# Estructura (validada en staging):
#  - Folio de lote:  MMAA/NN/DO5  (reinicio mensual del consecutivo)
#  - Receta (por prueba): solo las 5 hojas maestras a 4 cm (10 tiras x 0.4 cm)
#       SPHMC10 THC, SPHMC11 AMP, SPHMC12 COC, SPHMC13 MET, SPHMC14 OPI
#  - Operaciones: identicas a DMIVU01 (7 pasos, tiempos 1 min)
#  - Presentacion: 1 kit = tubo STTBT01 + desecante STDSC01 + bolsa hibrida
#       COBHI01 + manual MIMAN01  (package_qty=1)
#  - QC: requiere analisis de producto terminado
Pt = env['product.template']
Bom = env['mrp.bom']
Op = env['mrp.routing.workcenter']
Pres = env['amunet.packaging.presentation']
Comp = env['amunet.packaging.presentation.component']
Prod = env['product.product']
Uom = env['uom.uom']

o = Pt.search([('default_code', '=', 'DMADO02')], limit=1)
patt = Pt.search([('default_code', '=', 'DMADB01')], limit=1)   # patron antidoping (flags/secuencia/presentacion)
ref = Pt.search([('default_code', '=', 'DMIVU01')], limit=1)     # referencia de operaciones
if not (o and patt and ref):
    raise Exception("Falta DMADO02, DMADB01 o DMIVU01 en prod")
vo = o.product_variant_id
cm = Uom.search([('name', '=', 'cm')], limit=1)
print("DMADO02 id=%s | DMADB01 id=%s | DMIVU01 id=%s" % (o.id, patt.id, ref.id))

# 1) Alinear flags de producto (sin tocar name/code)
CAMPOS = ['categ_id', 'uom_id', 'type', 'tracking', 'is_storable', 'sale_ok',
          'purchase_ok', 'amunet_req_quality_control', 'qc_required']
vals = {}
for f in CAMPOS:
    if f in patt._fields and f in o._fields:
        v = patt[f]
        vals[f] = v.id if hasattr(v, 'id') else v
o.write(vals)
print("  flags alineados")

# 2) Secuencia de folio /DO5
if not o.mo_sequence_id and patt.mo_sequence_id:
    s = patt.mo_sequence_id.copy({
        'name': 'Lote kit terminado - Antidoping Orina 5P',
        'suffix': '/DO5', 'number_next': 1,
    })
    if 'amunet_last_period' in s._fields:
        s.amunet_last_period = False
    o.mo_sequence_id = s.id
    print("  secuencia /DO5 creada")
else:
    print("  secuencia: ya existia")

# 3) BoM: 5 hojas x 4 cm + operaciones identicas a DMIVU01
if not Bom.search([('product_tmpl_id', '=', o.id)], limit=1):
    nuevo = Bom.create({
        'product_tmpl_id': o.id,
        'product_id': vo.id,
        'product_qty': 1.0,
        'type': 'normal',
    })
    for code in ['SPHMC10', 'SPHMC11', 'SPHMC12', 'SPHMC13', 'SPHMC14']:
        cp = Prod.search([('default_code', '=', code)], limit=1)
        env['mrp.bom.line'].create({
            'bom_id': nuevo.id, 'product_id': cp.id,
            'product_qty': 4, 'product_uom_id': cm.id,
        })
    bom_ref = Bom.search([('product_tmpl_id', '=', ref.id)], limit=1)
    for op in bom_ref.operation_ids.sorted('sequence'):
        Op.create({
            'bom_id': nuevo.id, 'name': op.name,
            'workcenter_id': op.workcenter_id.id, 'sequence': op.sequence,
            'time_cycle_manual': op.time_cycle_manual, 'time_mode': op.time_mode,
        })
    print("  BoM creada: comp=%s ops=%s" % (len(nuevo.bom_line_ids), len(nuevo.operation_ids)))
else:
    print("  BoM: ya existe")

# 4) Presentacion (1 kit) + componentes
if not Pres.search([('product_tmpl_id', '=', o.id)], limit=1):
    pres_patt = Pres.search([('product_tmpl_id', '=', patt.id)], limit=1)
    np = pres_patt.copy({
        'product_tmpl_id': o.id,
        'product_id': (vo.id if 'product_id' in pres_patt._fields and pres_patt.product_id else False),
        'name': 'Antidoping Orina 5P - tubo con 50 tiras',
        'package_qty': 1,
    })
    for fld in ('box_component_id', 'label_component_id', 'manual_component_id'):
        if fld in np._fields:
            np[fld] = False
    if np.component_ids:
        np.component_ids.unlink()
    for code, q in [('STTBT01', 1), ('STDSC01', 1), ('COBHI01', 1), ('MIMAN01', 1)]:
        cp = Prod.search([('default_code', '=', code)], limit=1)
        Comp.create({'presentation_id': np.id, 'product_id': cp.id, 'qty_per_box': q})
    print("  presentacion creada: pkg=%s comp=%s" % (np.package_qty, len(np.component_ids)))
else:
    print("  presentacion: ya existe")

env.cr.commit()

# Verificacion final
bom = Bom.search([('product_tmpl_id', '=', o.id)], limit=1)
pres = Pres.search([('product_tmpl_id', '=', o.id)], limit=1)
print("VERIF DMADO02: folio=%s%s comp=%s ops=%s present=%s pkg=%s comp_pres=%s" % (
    o.mo_sequence_id.prefix, o.mo_sequence_id.suffix,
    len(bom.bom_line_ids), len(bom.operation_ids),
    bool(pres), pres.package_qty if pres else '-',
    [x.product_id.default_code for x in pres.component_ids] if pres else []))
print("Operaciones:")
for op in bom.operation_ids.sorted('sequence'):
    print("  %2d %-4s %s" % (op.sequence, op.workcenter_id.code, op.name))
print("LISTO")
