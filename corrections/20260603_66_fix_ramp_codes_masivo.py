"""
Corrige masivamente los códigos RAMP/CERMP de todos los cartuchos
basándose en el conteo de ventanas que ya está en las descripciones.
Regla: impar (1,3,5 ventanas) → RAMP-004/CERMP-004, par (2,4) → RAMP-005/CERMP-005
"""
import re

templates = env['product.template'].search([
    ('categ_id.name', '=', 'Cartucho'),
    ('report_document_code', '!=', False),
])

corrected = []
skipped_no_desc = []
skipped_no_match = []
already_ok = []

for pt in templates:
    code = pt.default_code or ''
    desc = pt.description or ''
    # La descripción está en HTML: "Cartucho de plástico de N ventana(s)..."
    m = re.search(r'de\s+(\d+)\s+ventana', desc, re.IGNORECASE)
    if not m:
        skipped_no_match.append(f"  {code:<10} {str(pt.name)[:45]} (sin coincidencia)")
        continue

    ventanas = int(m.group(1))
    es_impar = (ventanas % 2 != 0)
    ramp_correcto  = 'RAMP-004'  if es_impar else 'RAMP-005'
    cermp_correcto = 'CERMP-004' if es_impar else 'CERMP-005'

    if pt.report_document_code == ramp_correcto and pt.certificate_document_code == cermp_correcto:
        already_ok.append(code)
        continue

    old_ramp  = pt.report_document_code or ''
    old_cermp = pt.certificate_document_code or ''
    pt.write({'report_document_code': ramp_correcto, 'certificate_document_code': cermp_correcto})
    corrected.append(
        f"  {code:<10} {ventanas}V {'impar' if es_impar else 'par  '} "
        f"{old_ramp} → {ramp_correcto}  |  {old_cermp} → {cermp_correcto}  | {str(pt.name)[:35]}"
    )

env.cr.commit()

print(f"=== CORREGIDOS: {len(corrected)} ===")
for l in corrected:
    print(l)

print(f"\n=== YA ESTABAN CORRECTOS: {len(already_ok)} ===")
print(f"  {', '.join(already_ok)}")

print(f"\n=== SIN DESCRIPCIÓN (no se tocaron): {len(skipped_no_match)} ===")
for l in skipped_no_match:
    print(l)

print("\nListo.")
