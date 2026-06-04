"""
Marca como obligatorios Largo, Ancho y CV en todos los cartuchos.
Observaciones queda opcional.
RE-EJECUTABLE tras refrescos de staging.
"""

REQUIRED_CODES = ['external_length', 'external_width', 'cv_percent']

cartuchos = env['product.template'].search([
    ('categ_id.name', '=', 'Cartucho'),
    ('qc_required', '=', True),
])

updated = 0
for pt in cartuchos:
    for config in pt.additional_info_config_ids:
        if config.field_id.code in REQUIRED_CODES and not config.required:
            config.write({'required': True})
            updated += 1

env.cr.commit()
print(f"Campos marcados como obligatorios: {updated}")
print("Listo.")
