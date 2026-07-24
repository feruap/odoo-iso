# -*- coding: utf-8 -*-
# Completa la estructura de PTREC03 "Medio de cultivo para E. coli" replicando
# PTREC01 (Salmonela): secuencia de folio (/R03), BoM (3 comp + 7 operaciones),
# presentacion (10 piezas + COBME02) y flags de producto/QC.
# El producto PTREC03 YA existe (cascaron). Autorizado por Fernando 2026-07-13.
# Idempotente: no duplica lo que ya exista.
Pt = env['product.template']
Bom = env['mrp.bom']
Pres = env['amunet.packaging.presentation']
Comp = env['amunet.packaging.presentation.component']

pt01 = Pt.search([('default_code', '=', 'PTREC01')], limit=1)
pt03 = Pt.search([('default_code', '=', 'PTREC03')], limit=1)
if not (pt01 and pt03):
    raise Exception("Falta PTREC01 o PTREC03 en prod")
v03 = pt03.product_variant_id
print("PTREC01 id=%s | PTREC03 id=%s" % (pt01.id, pt03.id))

# 1) Alinear flags del producto (sin tocar name/code)
CAMPOS = ['categ_id', 'uom_id', 'type', 'tracking', 'is_storable', 'sale_ok', 'purchase_ok',
          'amunet_req_quality_control', 'amunet_req_history_log', 'amunet_req_calculations',
          'amunet_req_dilution', 'amunet_req_aforar', 'use_expiration_date', 'expiration_time']
vals = {}
for f in CAMPOS:
    if f in pt01._fields and f in pt03._fields:
        v = pt01[f]
        vals[f] = v.id if hasattr(v, 'id') else v
pt03.write(vals)
print("  flags alineados")

# 2) Secuencia de folio (/R03)
if not pt03.mo_sequence_id and pt01.mo_sequence_id:
    s = pt01.mo_sequence_id.copy({
        'name': 'Lote kit terminado - Medio de Cultivo para E. coli',
        'suffix': '/R03', 'number_next': 1,
    })
    pt03.mo_sequence_id = s.id
    print("  secuencia /R03 creada")
else:
    print("  secuencia: ya existia o PTREC01 sin secuencia")

# 3) BoM (lineas + operaciones), renombrando a E. coli
if not Bom.search([('product_tmpl_id', '=', pt03.id)], limit=1):
    bom01 = Bom.search([('product_tmpl_id', '=', pt01.id)], limit=1)
    nuevo = bom01.copy({
        'product_tmpl_id': pt03.id,
        'product_id': v03.id if bom01.product_id else False,
    })
    for op in nuevo.operation_ids:
        if op.name:
            op.name = op.name.replace('Salmonella', 'E. coli').replace('Salmonela', 'E. coli')
    print("  BoM creada: comp=%s ops=%s" % (len(nuevo.bom_line_ids), len(nuevo.operation_ids)))
else:
    print("  BoM: ya existe")

# 4) Presentacion + componentes
pres03 = Pres.search([('product_tmpl_id', '=', pt03.id)], limit=1)
if not pres03:
    pres01 = Pres.search([('product_tmpl_id', '=', pt01.id)], limit=1)
    if pres01:
        pres03 = pres01.copy({
            'product_tmpl_id': pt03.id,
            'product_id': v03.id if 'product_id' in pres01._fields and pres01.product_id else False,
            'name': 'Medio de Cultivo E. coli 10 piezas',
        })
        print("  Presentacion creada")
if pres03 and not pres03.component_ids:
    pres01 = Pres.search([('product_tmpl_id', '=', pt01.id)], limit=1)
    for c in pres01.component_ids:
        Comp.create({'presentation_id': pres03.id, 'product_id': c.product_id.id, 'qty_per_box': c.qty_per_box})
    print("  componentes de presentacion agregados")

env.cr.commit()
# Verificacion
bom3 = Bom.search([('product_tmpl_id', '=', pt03.id)], limit=1)
pres = Pres.search([('product_tmpl_id', '=', pt03.id)], limit=1)
print("VERIF PTREC03: folio=%s%s comp=%s ops=%s present=%s pkg=%s comp_pres=%s" % (
    pt03.mo_sequence_id.prefix, pt03.mo_sequence_id.suffix,
    len(bom3.bom_line_ids), len(bom3.operation_ids),
    bool(pres), pres.package_qty if pres else '-',
    [(x.product_id.default_code, x.qty_per_box) for x in pres.component_ids] if pres else []))
print("LISTO")
