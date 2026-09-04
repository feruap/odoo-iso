"""
Buscar producto 'hilera chica' y su configuración de MAVI-11 y VAMA-023.
"""
import json

ProdTmpl = env['product.template']
Param    = env['amunet.quality.check.parameter']
Rel      = env['amunet.quality.parameter.product.rel']
SpecConf = env['amunet.quality.parameter.specification.config']
QPoint   = env['amunet.quality.point']

# Buscar producto
prods = ProdTmpl.with_context(active_test=False).search([('name', 'ilike', 'hilera')])
print(f"Productos con 'hilera': {len(prods)}")
for p in prods:
    print(f"  id={p.id} '{p.default_code}' '{p.name}' activo={p.active}")

print()

# Ver parámetros de cada uno
param_mavi11 = Param.search([('code', '=', 'MAVI-11')], limit=1)
param_vama023 = Param.search([('code', '=', 'VAMA-023')], limit=1)
print(f"MAVI-11 id={param_mavi11.id if param_mavi11 else 'NO'}")
print(f"VAMA-023 id={param_vama023.id if param_vama023 else 'NO'}")

for p in prods:
    print(f"\n── {p.name} ({p.default_code}) ──")
    rels = Rel.with_context(active_test=False).search([('product_tmpl_id', '=', p.id)])
    for r in rels:
        specs = SpecConf.with_context(active_test=False).search([
            ('product_parameter_rel_id', '=', r.id)
        ])
        for s in specs:
            print(f"  {r.parameter_id.code} / {s.specification_id.name if s.specification_id else s.name}")
            print(f"    criterio: {s.acceptance_criteria}")
            print(f"    activo: {s.active} | tipo: {s.evaluation_type}")
            if s.text_phrase_mapping:
                try:
                    m = json.loads(s.text_phrase_mapping)
                    for pos in m.get('positions', []):
                        label = pos.get('label','')
                        min_v = pos.get('min_value','')
                        max_v = pos.get('max_value','')
                        nom   = pos.get('nominal','')
                        tol   = pos.get('tolerance','')
                        print(f"      pos: {label} | min={min_v} max={max_v} nom={nom} tol={tol}")
                except: pass
