"""Ver campos actuales de los detalles MAVI-11 del análisis 776."""
Detail = env['amunet.quality.test.line.detail']
Line   = env['amunet.quality.test.line']

# Detalles MAVI-11
for det_id in [6545, 6546, 6547, 6548, 7582]:
    d = Detail.browse(det_id)
    print(f"[{d.id}] '{d.name}'")
    print(f"  acceptance_criteria: '{d.acceptance_criteria}'")
    print(f"  min_value: {d.min_value} | max_value: {d.max_value}")
    print(f"  evaluation_type: {d.evaluation_type}")

# Ver la línea VAMA-023
print("\n── VAMA-023 ──")
linea = Line.browse(2289)
print(f"Línea [{linea.id}] verdict={linea.verdict} | activa={linea.active if hasattr(linea,'active') else 'N/A'}")
campos_linea = [(n, str(f.type)) for n, f in linea._fields.items() 
                if 'active' in n or 'visible' in n or 'hidden' in n]
print("Campos de visibilidad:", campos_linea)
