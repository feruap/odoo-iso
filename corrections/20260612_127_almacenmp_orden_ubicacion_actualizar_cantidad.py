# Orden en "Actualizar cantidad": AMP/Existencias siempre antes que AMPB/Existencias
# Causa raíz: en PostgreSQL en_US.utf8, "AMPB/" ordena antes que "AMP/" porque "B" < "/"
# Solución: location_id DESC invierte el orden, poniendo AMP primero

base_view = env['ir.ui.view'].search([
    ('name', '=', 'stock.quant.inventory.list.editable'),
    ('model', '=', 'stock.quant'),
], limit=1)

if not base_view:
    print("ERROR: No se encontró la vista base")
else:
    existe = env['ir.ui.view'].search([
        ('name', '=', 'stock.quant.inventory.list.order.almacenmp'),
    ], limit=1)

    arch = '''<data>
    <xpath expr="." position="attributes">
        <attribute name="default_order">location_id desc, product_id, lot_id</attribute>
    </xpath>
</data>'''

    if existe:
        existe.write({'arch_db': arch})
        print("Vista actualizada con location_id DESC (id=" + str(existe.id) + ")")
    else:
        nueva = env['ir.ui.view'].create({
            'name': 'stock.quant.inventory.list.order.almacenmp',
            'model': 'stock.quant',
            'inherit_id': base_view.id,
            'arch_db': arch,
            'priority': 120,
        })
        print("Vista creada con location_id DESC (id=" + str(nueva.id) + ")")

    env.cr.commit()
    print("COMMIT OK")
