# Muestra los flags de los consumibles EPP para entender qué campo controla el ruteo
prods = env['product.template'].search([
    ('default_code', 'in', ['COGEC01', 'COGME01', 'COCOF01', 'COCRP01'])
])
for p in prods:
    print(f"[{p.default_code}] {p.name}")
    print(f"  amunet_requires_quarantine={p.amunet_requires_quarantine}")
    print(f"  amunet_req_quality_control={getattr(p, 'amunet_req_quality_control', 'N/A')}")
    print(f"  categ.amunet_requires_quarantine={p.categ_id.amunet_requires_quarantine}")
    print(f"  _effective_requires_quarantine()={p._amunet_effective_requires_quarantine()}")
