"""Verificar todos los campos relevantes de las líneas nuevas."""
QLine = env['amunet.quality.test.line']
for lid in [2635, 2636]:
    line = QLine.browse(lid)
    print(f"Line {lid}:")
    print(f"  name={repr(line.name)}")
    print(f"  code={repr(line.code)}")
    print(f"  parameter_id={line.parameter_id.id if line.parameter_id else 'VACÍO'} ({line.parameter_id.code if line.parameter_id else 'VACÍO'})")
    print(f"  parameter_rel_id={line.parameter_rel_id.id if line.parameter_rel_id else 'VACÍO'}")
    print(f"  has_details={line.has_details}")
    print(f"  detail_count={line.detail_count}")
