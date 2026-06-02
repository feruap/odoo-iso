
# Impares (ventanas totales impares: 1, 3, 5, 7) → RAMP-004 / CERMP-004
# Fuente: F-CC-007-001 Descripción y especificación de cartuchos
IMPARES_KEYWORDS = [
    'coronavirus',
    'influenza',
    'dengue igG/IgM',
    'dengue igg',
    'dengue igm',
    'estreptococcus b',
    'antidoping 5p',
    'antidoping 3p',
    'chikungunya',
    'zika igg',
    'zika igm',
    'ph vaginal',
]

CODE_IMPAR  = ('RAMP-004', 'CERMP-004')
CODE_PAR    = ('RAMP-005', 'CERMP-005')

templates = env['product.template'].search([('categ_id.name', '=', 'Cartucho')])
print(f"Total cartuchos en categoria 'Cartucho': {len(templates)}")

updated_impar = []
updated_par   = []
skipped       = []

for pt in templates:
    name = (pt.name or '').lower()

    is_impar = any(kw.lower() in name for kw in IMPARES_KEYWORDS)
    code_r, code_c = CODE_IMPAR if is_impar else CODE_PAR

    old_r = pt.report_document_code or ''
    old_c = pt.certificate_document_code or ''

    if old_r == code_r and old_c == code_c:
        skipped.append(pt.name)
        continue

    pt.write({
        'report_document_code':      code_r,
        'certificate_document_code': code_c,
    })

    label = f"  {'IMPAR' if is_impar else 'PAR  '} | {pt.name[:55]:<55} | {old_r or '---':>8} → {code_r}"
    if is_impar:
        updated_impar.append(label)
    else:
        updated_par.append(label)

env.cr.commit()

print(f"\n=== IMPARES → RAMP-004/CERMP-004 ({len(updated_impar)} actualizados) ===")
for l in updated_impar: print(l)
print(f"\n=== PARES → RAMP-005/CERMP-005 ({len(updated_par)} actualizados) ===")
for l in updated_par: print(l)
print(f"\n=== Sin cambio (ya tenían el código correcto): {len(skipped)} ===")
print("Listo.")
