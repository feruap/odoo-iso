# Corrige 4 productos cuyo código RAMP/CERMP no coincide con el Excel de Diana
# Fuente: Cartuchos.xlsx (nc-calidad:/Odoo/CONTROL DE CALIDAD/MATERIA PRIMA/Cartuchos/)

corrections = [
    # (default_code, ramp_correcto, cermp_correcto)
    ('MPCAR01',  'RAMP-004', 'CERMP-004'),   # Covid Ag: 1 ventana, 1 control → impar
    ('MPCAR53',  'RAMP-005', 'CERMP-005'),   # Antidoping 5P: 2 ventanas, 2 controles → par
    ('MPCAR55',  'RAMP-004', 'CERMP-004'),   # Calprotectina: 1 ventana, 1 control → impar
    ('MPCAC10',  'RAMP-004', 'CERMP-004'),   # Antidoping cabello: 3 ventanas, 3 controles → impar
]

updated = []
for code, ramp, cermp in corrections:
    pt = env['product.template'].search([('default_code', '=', code)], limit=1)
    if not pt:
        print(f"  NO ENCONTRADO: {code}")
        continue
    old_ramp  = pt.report_document_code or ''
    old_cermp = pt.certificate_document_code or ''
    pt.write({'report_document_code': ramp, 'certificate_document_code': cermp})
    updated.append(f"  {code:<10} {str(pt.name)[:40]:<42} {old_ramp} → {ramp}  |  {old_cermp} → {cermp}")

env.cr.commit()

print(f"Actualizados: {len(updated)}")
for l in updated:
    print(l)
print("Listo.")
