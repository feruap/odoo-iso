"""
Asigna a todos los cartuchos los campos de información adicional:
  - Largo externo (external_length, ID 4)
  - Ancho externo (external_width, ID 5)
  - Coeficiente de variación (cv_percent, ID 2)
Y activa require_additional_info en cada uno.
"""

FIELD_CODES = ['external_length', 'external_width', 'cv_percent']

fields_map = {}
for code in FIELD_CODES:
    f = env['amunet.quality.additional.info.field'].search([('code', '=', code)], limit=1)
    if not f:
        print(f"CAMPO NO ENCONTRADO: {code}")
    else:
        fields_map[code] = f
        print(f"  Campo OK: {code} → ID {f.id}")

if len(fields_map) != len(FIELD_CODES):
    print("ERROR: faltan campos. Abortando.")
    raise SystemExit(1)

cartuchos = env['product.template'].search([('categ_id.name', '=', 'Cartucho')])
print(f"\nCartuchos encontrados: {len(cartuchos)}")

Config = env['amunet.quality.additional.info.config']

added = []
skipped_already = []

skipped_no_qc = []

for pt in sorted(cartuchos, key=lambda x: x.default_code or ''):
    code = pt.default_code or f'(sin código, id={pt.id})'

    # Solo procesar los que tienen QC requerido
    if not pt.qc_required:
        skipped_no_qc.append(code)
        continue

    # Activar require_additional_info
    if not pt.require_additional_info:
        pt.write({'require_additional_info': True})

    existing_codes = set(pt.additional_info_config_ids.mapped('field_id.code'))
    new_fields = [f for c, f in fields_map.items() if c not in existing_codes]

    if not new_fields:
        skipped_already.append(code)
        continue

    for seq, field in enumerate(new_fields, start=len(existing_codes) + 1):
        Config.create({
            'product_tmpl_id': pt.id,
            'field_id': field.id,
            'sequence': seq,
            'required': False,
            'active': True,
        })
    added.append(f"  {code:<12} +{[f.code for f in new_fields]}")

env.cr.commit()

print(f"\n=== CONFIGURADOS: {len(added)} ===")
for l in added:
    print(l)
print(f"\n=== YA TENÍAN LOS TRES CAMPOS: {len(skipped_already)} ===")
print(f"  {', '.join(skipped_already)}")
print(f"\n=== SIN QC REQUERIDO (no modificados): {len(skipped_no_qc)} ===")
print(f"  {', '.join(skipped_no_qc)}")
print("Listo.")
