"""Verificar nombres de líneas recién creadas."""
QLine  = env['amunet.quality.test.line']
QDetail = env['amunet.quality.test.line.detail']

for lid in [2635, 2636]:
    line = QLine.browse(lid)
    if line.exists():
        print(f"Line {lid}: name={repr(line.name)} param={line.parameter_rel_id.parameter_id.name if line.parameter_rel_id else 'N/A'}")
        for d in line.detail_line_ids:
            print(f"  Detail {d.id}: name={repr(d.name)} eval={d.evaluation_type}")
    else:
        print(f"Line {lid}: no existe")
