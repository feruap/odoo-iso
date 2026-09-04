"""Diagnóstico: buscar MAVI-13 y MGA-0981 en el sistema."""
import json

Param = env['amunet.quality.check.parameter']
SpecBase = env['amunet.quality.check.parameter.specification']

# Buscar MAVI-13
mavi13 = Param.with_context(active_test=False).search([('code', 'like', 'MAVI-13')], limit=5)
print("=== MAVI-13 ===")
for p in mavi13:
    print(f"  id={p.id} code={p.code} name={p.name} active={p.active}")
    specs = SpecBase.with_context(active_test=False).search([('parameter_id','=',p.id)])
    for s in specs:
        print(f"    spec id={s.id} name={s.name} eval={s.evaluation_type} active={s.active}")

# Buscar MGA-0981
mga = Param.with_context(active_test=False).search([('code', 'like', 'MGA')], limit=10)
print("\n=== MGA parámetros ===")
for p in mga:
    print(f"  id={p.id} code={p.code} name={p.name} active={p.active}")
    specs = SpecBase.with_context(active_test=False).search([('parameter_id','=',p.id)])
    for s in specs:
        print(f"    spec id={s.id} name={s.name} eval={s.evaluation_type} active={s.active}")

# Estado actual del análisis 785
QCheck = env['amunet.quality.check']
check = QCheck.browse(785)
print(f"\n=== Análisis 785 estado={check.state} ===")
for line in check.test_line_ids:
    print(f"  line id={line.id} name={line.name} verdict={line.verdict}")
    for d in line.detail_line_ids:
        print(f"    detail id={d.id} name={d.name} eval={d.evaluation_type}")

