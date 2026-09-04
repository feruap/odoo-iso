"""
Diagnóstico completo del estado de controles negativos en producción.
"""
import json

QCheck = env['amunet.quality.check']
ProdTmpl = env['product.template']
Rel = env['amunet.quality.parameter.product.rel']
SpecConf = env['amunet.quality.parameter.specification.config']
Line = env['amunet.quality.test.line']

# 1. Ver líneas de QC/2026/00041
print("── QC/2026/00041 (análisis 785) — líneas de prueba ──")
check = QCheck.browse(785)
for line in check.test_line_ids:
    print(f"  [{line.id}] {line.name} | param: {line.parameter_id.code if line.parameter_id else '-'} | verdict: {line.verdict}")
    for det in line.detail_line_ids:
        et = det.evaluation_type
        has_mapping = bool(det.text_phrase_mapping)
        print(f"    det [{det.id}] {det.name} | tipo: {et} | mapping: {has_mapping}")
        if has_mapping:
            try:
                m = json.loads(det.text_phrase_mapping)
                fst = m.get('fixed_sample_type','libre')
                pos = len(m.get('positions', []))
                print(f"      → fixed_sample_type: {fst} | posiciones: {pos}")
            except: pass

# 2. Buscar si el script creó productos STCON01/SPCNL04 nuevos (activos)
print("\n── Buscar STCON01/SPCNL04 activos en producción ──")
for codigo in ['STCON01', 'SPCNL04']:
    todos = ProdTmpl.with_context(active_test=False).search([('default_code', '=', codigo)])
    for t in todos:
        rels = Rel.search([('product_tmpl_id', '=', t.id)])
        checks = QCheck.with_context(active_test=False).search([('product_id.product_tmpl_id', '=', t.id)])
        print(f"  {codigo} id={t.id} activo={t.active} nombre='{t.name}' params={rels.mapped('parameter_id.code')} análisis={len(checks)}")

# 3. Ver si hay algún producto activo con código 'STCON01' o similar creado recientemente
print("\n── Productos de Control Negativo activos en producción ──")
cnl_prods = ProdTmpl.search([('name', 'ilike', 'control negativo'), ('active', '=', True)])
for t in cnl_prods:
    rels = Rel.search([('product_tmpl_id', '=', t.id)])
    print(f"  id={t.id} '{t.default_code}' '{t.name}' params={rels.mapped('parameter_id.code')}")
