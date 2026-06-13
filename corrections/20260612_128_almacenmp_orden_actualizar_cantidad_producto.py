# Corregir orden en "Actualizar Cantidad" abierto desde formulario de producto
# La vista que se usa desde el botón del producto es stock.quant.list.editable (id=1153),
# NO la de inventario físico (id=1159). Necesita su propio override de default_order.
# Objetivo: AMP/Existencias siempre antes que AMPB/Existencias (location_id DESC invierte
# el orden del locale PostgreSQL en_US.utf8 donde "/" < "B")

VIEW_BASE_XML_ID = 'stock.view_stock_quant_tree_editable'
VIEW_NAME = 'stock.quant.list.order.almacenmp.producto'
PRIORITY = 120

arch = '''<data>
    <xpath expr="." position="attributes">
        <attribute name="default_order">location_id desc, product_id, lot_id</attribute>
    </xpath>
</data>'''

view_base = env.ref(VIEW_BASE_XML_ID)
existe = env['ir.ui.view'].search([('name', '=', VIEW_NAME)], limit=1)

if existe:
    existe.write({'arch_db': arch, 'priority': PRIORITY})
    print("Override ACTUALIZADO id=" + str(existe.id))
else:
    nuevo = env['ir.ui.view'].create({
        'name': VIEW_NAME,
        'model': 'stock.quant',
        'inherit_id': view_base.id,
        'priority': PRIORITY,
        'arch_db': arch,
        'active': True,
    })
    print("Override CREADO id=" + str(nuevo.id))

print("Vista base (id=" + str(view_base.id) + "): " + VIEW_BASE_XML_ID)
env.cr.commit()
print("COMMIT OK")
