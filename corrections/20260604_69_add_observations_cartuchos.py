"""
Agrega el campo Observaciones/Fotos (observations, html_attachments)
a todos los cartuchos que ya tienen QC requerido.
RE-EJECUTABLE tras refrescos de staging.
"""

obs_field = env['amunet.quality.additional.info.field'].search([('code', '=', 'observations')], limit=1)
if not obs_field:
    print("ERROR: campo 'observations' no encontrado")
    raise SystemExit(1)

print(f"Campo: {obs_field.name} (ID {obs_field.id})")

Config = env['amunet.quality.additional.info.config']
cartuchos = env['product.template'].search([
    ('categ_id.name', '=', 'Cartucho'),
    ('qc_required', '=', True),
])

added = []
skipped = []

for pt in sorted(cartuchos, key=lambda x: x.default_code or ''):
    existing_codes = pt.additional_info_config_ids.mapped('field_id.code')
    if 'observations' in existing_codes:
        skipped.append(pt.default_code or str(pt.id))
        continue
    seq = len(pt.additional_info_config_ids) + 1
    Config.create({
        'product_tmpl_id': pt.id,
        'field_id': obs_field.id,
        'sequence': seq,
        'required': False,
        'active': True,
    })
    added.append(pt.default_code or str(pt.id))

env.cr.commit()
print(f"\nAgregado a {len(added)} cartuchos: {', '.join(added[:10])}{'...' if len(added)>10 else ''}")
print(f"Ya tenían: {len(skipped)}")
print("Listo.")
