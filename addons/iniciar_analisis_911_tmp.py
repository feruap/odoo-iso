Check = env['amunet.quality.check']
check = Check.browse(911)
print(f"Análisis: {check.analysis_number} (id={check.id}), estado actual: {check.state}")

# Iniciar directamente sin muestreo
if check.state == 'draft':
    check.write({'state': 'in_progress', 'qty_sampling': 5})
    env.cr.commit()
    print(f"✓ Estado actualizado a: {check.state}")
    print(f"  Parámetros: {len(check.test_line_ids)}")
    for tl in check.test_line_ids.sorted('sequence'):
        print(f"  [{tl.sequence}] {tl.code} — {tl.name}")
else:
    print(f"Ya está en estado: {check.state}")
