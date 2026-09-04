"""
Verificar estado actual en producción de los controles negativos
y el análisis 785 (STCNL01).
"""

QCheck = env['amunet.quality.check']
ProdTmpl = env['product.template']
Param = env['amunet.quality.check.parameter']
Rel = env['amunet.quality.parameter.product.rel']

# 1. Ver análisis 785
check785 = QCheck.browse(785)
print(f"Análisis 785:")
print(f"  Nombre: {check785.name}")
print(f"  Producto: {check785.product_id.default_code} — {check785.product_id.name}")
print(f"  Estado: {check785.state}")
print(f"  Líneas de prueba: {len(check785.test_line_ids)}")
for line in check785.test_line_ids:
    print(f"    - {line.name} | verdict={line.verdict}")
print()

# 2. Ver si STCNL01 existe como producto
for codigo in ['STCNL01', 'STCON01', 'SPCNL04']:
    tmpl = ProdTmpl.with_context(active_test=False).search([('default_code', '=', codigo)], limit=1)
    if tmpl:
        # Ver si tiene parámetros configurados
        rels = Rel.search([('product_tmpl_id', '=', tmpl.id)])
        params = rels.mapped('parameter_id.code')
        print(f"{codigo}: id={tmpl.id} activo={tmpl.active} params={params}")
        # Ver sus análisis
        checks = QCheck.with_context(active_test=False).search([('product_id.product_tmpl_id', '=', tmpl.id)])
        print(f"  Análisis: {len(checks)}")
        for c in checks:
            print(f"    {c.name} | {c.state} | líneas: {len(c.test_line_ids)}")
    else:
        print(f"{codigo}: NO ENCONTRADO")
