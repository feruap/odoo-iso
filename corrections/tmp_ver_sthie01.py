"""
Ver configuración completa de MAVI-11 y VAMA-023 en STHIE01 (Hielera chica).
"""
import json

ProdTmpl = env['product.template']
Rel      = env['amunet.quality.parameter.product.rel']
SpecConf = env['amunet.quality.parameter.specification.config']

t = ProdTmpl.with_context(active_test=False).browse(988)  # STHIE01
print(f"Producto: {t.default_code} — {t.name}")
print()

rels = Rel.with_context(active_test=False).search([('product_tmpl_id', '=', 988)])
for r in rels:
    specs = SpecConf.with_context(active_test=False).search([
        ('product_parameter_rel_id', '=', r.id)
    ])
    print(f"Parámetro: {r.parameter_id.code} — {r.parameter_id.name}")
    for s in specs:
        spec_name = s.specification_id.name if s.specification_id else '-'
        print(f"  [{s.id}] activo={s.active} '{spec_name}' | criterio: '{s.acceptance_criteria}' | tipo: {s.evaluation_type}")
        if s.text_phrase_mapping:
            try:
                m = json.loads(s.text_phrase_mapping)
                for pos in m.get('positions', []):
                    print(f"    pos {pos.get('index','')} {pos.get('label','')} | min={pos.get('min_value','')} max={pos.get('max_value','')} nom={pos.get('nominal','')} tol={pos.get('tolerance','')}")
            except Exception as e:
                print(f"    (parse error: {e})")
    print()
