"""Fix: lines 2635 y 2636 sin parameter_id → code aparece False."""
QLine = env['amunet.quality.test.line']
Rel   = env['amunet.quality.parameter.product.rel']

fixes = [
    (2635, 4200),  # MGA-0981
    (2636, 4201),  # MAVI-13
]
for line_id, rel_id in fixes:
    rel  = Rel.browse(rel_id)
    line = QLine.browse(line_id)
    param = rel.parameter_id
    line.write({'parameter_id': param.id})
    print(f"  Line {line_id}: parameter_id={param.id} code={line.code} name={line.name}")

env.cr.commit()
print("✓ Listo.")
