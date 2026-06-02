"""Archivar producto huérfano 'Bolsas Termosellables' sin código ni categoría.

Producto creado por OdooBot el 2026-01-17, sin default_code, sin categoría,
sin movimientos y sin lotes. Duplicado incompleto de la familia MPBOL01-05.
Se archiva para evitar confusión en recepciones y catálogo.
"""

pt = env['product.template'].sudo().search([
    ('name->>', 'en_US', '=', 'Bolsas Termosellables'),
    ('default_code', '=', False),
    ('active', '=', True),
], limit=1)

if not pt:
    print("[YA ARCHIVADO o NO ENCONTRADO]")
else:
    moves = env['stock.move'].sudo().search_count([
        ('product_id.product_tmpl_id', '=', pt.id)
    ])
    if moves > 0:
        print(f"[OMITIDO] El producto id={pt.id} tiene {moves} movimientos — revisar manualmente.")
    else:
        pt.write({'active': False})
        env.cr.commit()
        print(f"[ARCHIVADO] id={pt.id}: {pt.name}")
